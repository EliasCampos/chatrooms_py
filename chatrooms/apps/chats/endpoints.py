from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from tortoise.exceptions import DoesNotExist

from chatrooms.apps.chats import services as chat_services
from chatrooms.apps.chats.schemas import (
    ChatCreate, ChatDetail, ChatOwn, ChatJoinResult, ChatMessageDetail,
)
from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.chats.websockets import get_ws_user
from chatrooms.apps.common.pagination import paginate_queryset
from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User


chats_router = APIRouter()


@chats_router.post('/', status_code=status.HTTP_201_CREATED, response_model=ChatDetail)
async def create_chat(chat_data: ChatCreate, user: User = Depends(get_current_user)):
    chat = await chat_services.create_chat(chat_data, user)
    return ChatDetail.from_orm(chat)


@chats_router.delete('/{chat_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: UUID, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    await chat_services.delete_chat(chat, user)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    await chat_services.join_chat(chat, user)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    return ChatDetail.from_orm(chat)


@chats_router.websocket('/ws/{chat_id}')
async def send_chat_messages(websocket: WebSocket, chat_id: UUID, user: Optional[User] = Depends(get_ws_user)):
    if not user:
        return

    try:
        chat = await Chat.available_to_user(user).get(id=chat_id)
    except DoesNotExist:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await chat_services.handle_chat_connection(chat, user, websocket)


@chats_router.get('/{chat_id}/messages', response_model=List[ChatMessageDetail])
async def list_chat_messages(chat_id: UUID, page: int = 1, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.available_to_user(user).select_related('creator').get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    qs = paginate_queryset(
        ChatMessage.filter(chat=chat).select_related('author').order_by('-id'),
        page_size=20, page=page,
    )

    messages = await qs
    return [ChatMessageDetail.from_orm(msg) for msg in messages]


@chats_router.delete('/{chat_id}/messages/{message_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_message(chat_id: UUID, message_id: int, user: User = Depends(get_current_user)):
    try:
        chat = await Chat.available_to_user(user).select_related('creator').get(id=chat_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    try:
        message = await ChatMessage.get(chat=chat, id=message_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat message not found.")

    await chat_services.delete_chat_message(message, user)
    return None
