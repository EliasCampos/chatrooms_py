from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket

from chatrooms.apps.chats.schemas import (
    ChatCreate, ChatDetail, ChatOwn, ChatJoinResult, ChatMessageCreate, ChatMessageDetail,
)
from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.chats.websockets import get_ws_user, chats_connections, get_event_payload
from chatrooms.apps.common.pagination import paginate_queryset
from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User
from pydantic import ValidationError
from starlette.status import (
    HTTP_201_CREATED, HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
    WS_1008_POLICY_VIOLATION, WS_1011_INTERNAL_ERROR,
)
from tortoise.exceptions import DoesNotExist


chats_router = APIRouter()


@chats_router.post('/', status_code=HTTP_201_CREATED, response_model=ChatDetail)
async def create_chat(chat_data: ChatCreate, user: User = Depends(get_current_user)):
    is_title_taken = await Chat.filter(creator=user, title=chat_data.title).exists()
    if is_title_taken:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={'title': "You already created chat with the title."},
        )

    chat = await Chat.create(**chat_data.dict(), creator=user)
    return ChatDetail.from_orm(chat)


@chats_router.delete('/{chat_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: UUID, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat not found.")

    if chat.creator_id != user.id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Can't delete not own chat")

    await chat.delete()
    await chats_connections.disconnect_chat(chat_id=chat_id, error_code=WS_1011_INTERNAL_ERROR)
    return None


@chats_router.get('/own', response_model=List[ChatOwn])
async def list_own_chats(page: int = 1, user: User = Depends(get_current_user)):
    qs = paginate_queryset(
        Chat.filter(creator=user).order_by('-created_at'),
        page_size=20, page=page,
    )

    chats = await qs
    return [ChatOwn.from_orm(chat) for chat in chats]


@chats_router.post('/{chat_id}/access', response_model=ChatJoinResult)
async def join_chat(chat_id: UUID, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat not found.")

    if chat.creator_id != user.id:
        await chat.participants.add(user)

    return {'detail': "Joined"}


@chats_router.get('/joined', response_model=List[ChatDetail])
async def list_joined_chats(page: int = 1, user: User = Depends(get_current_user)):
    qs = paginate_queryset(
        Chat.filter(participants=user).select_related('creator').order_by('title'),
        page_size=20, page=page,
    )

    chats = await qs
    return [ChatDetail.from_orm(chat) for chat in chats]


@chats_router.get('/{chat_id}', response_model=ChatDetail)
async def retrieve_chat_details(chat_id: UUID, user: User = Depends(get_current_user)):
    qs = Chat.available_to_user(user).select_related('creator')
    try:
        chat = await qs.get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat not found.")

    return ChatDetail.from_orm(chat)


@chats_router.websocket('/ws/{chat_id}')
async def send_chat_messages(websocket: WebSocket, chat_id: UUID, user: Optional[User] = Depends(get_ws_user)):
    if not user:
        return

    try:
        chat = await Chat.available_to_user(user).get(id=chat_id)
    except DoesNotExist:
        await websocket.close(code=WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    chats_connections.add_connection(chat.id, user.id, websocket)
    async for text in websocket.iter_text():
        try:
            message_data = ChatMessageCreate(text=text)
        except ValidationError as err:
            await websocket.send_text(get_event_payload(event='validation_error', payload=err.json()))
        else:
            chat_message = await ChatMessage.create(text=message_data.text, chat=chat, author=user)
            chat_message_payload = ChatMessageDetail.from_orm(chat_message)
            await chats_connections.send_chat_message(
                chat_id=chat.id, message=get_event_payload(event='new_message', payload=chat_message_payload.json()),
            )
    chats_connections.remove_connection(chat.id, user.id, websocket)


@chats_router.get('/{chat_id}/messages', response_model=List[ChatMessageDetail])
async def list_chat_messages(chat_id: UUID, page: int = 1, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.available_to_user(user).select_related('creator').get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat not found.")

    qs = paginate_queryset(
        ChatMessage.filter(chat=chat).select_related('author').order_by('-id'),
        page_size=20, page=page,
    )

    messages = await qs
    return [ChatMessageDetail.from_orm(msg) for msg in messages]


@chats_router.delete('/{chat_id}/messages/{message_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_chat_message(chat_id: UUID, message_id: int, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.available_to_user(user).select_related('creator').get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat not found.")

    try:
        message = await ChatMessage.get(chat=chat, id=message_id)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Chat message not found.")

    if message.author_id != user.id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Can't delete not own chat")

    message.text = ''
    message.is_deleted = True
    await message.save()
    return None
