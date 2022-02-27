import asyncio

from fastapi import status, WebSocket
from pydantic import ValidationError

from chatrooms.apps.chats.schemas import ChatCreate, ChatMessageCreate, ChatMessageDetail
from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.chats.websockets import chats_connections, get_event_payload
from chatrooms.apps.common.exceptions import BadInputError, PermissionDeniedError
from chatrooms.apps.users.models import User


async def create_chat(chat_data: ChatCreate, user: User) -> Chat:
    is_title_taken = await Chat.filter(creator=user, title=chat_data.title).exists()
    if is_title_taken:
        raise BadInputError({'title': "You already created chat with the title."})

    chat = await Chat.create(**chat_data.dict(), creator=user)
    return chat


async def delete_chat(chat: Chat, user: User) -> None:
    if chat.creator_id != user.id:
        raise PermissionDeniedError("Can't delete not own chat")

    await asyncio.gather(
        chat.delete(),
        chats_connections.disconnect_chat(chat_id=chat.id, error_code=status.WS_1011_INTERNAL_ERROR),
    )


async def join_chat(chat: Chat, user: User) -> None:
    if chat.creator_id != user.id:
        await chat.participants.add(user)


async def delete_chat_message(message: ChatMessage, user: User) -> None:
    if message.author_id != user.id:
        raise PermissionDeniedError("Can't delete not own chat")

    message.text = ''
    message.is_deleted = True
    await message.save()
    return None


async def handle_chat_connection(chat: Chat, user: User, websocket: WebSocket) -> None:
    chats_connections.add_connection(chat.id, user.id, websocket)
    async for text in websocket.iter_text():
        try:
            message_data = ChatMessageCreate(text=text)
        except ValidationError as err:
            await websocket.send_text(get_event_payload(event='validation_error', payload=err))
        else:
            chat_message = await ChatMessage.create(text=message_data.text, chat=chat, author=user)
            chat_message_payload = ChatMessageDetail.from_orm(chat_message)
            await chats_connections.send_chat_message(
                chat_id=chat.id, message=get_event_payload(event='new_message', payload=chat_message_payload),
            )
    chats_connections.remove_connection(chat.id, user.id, websocket)
