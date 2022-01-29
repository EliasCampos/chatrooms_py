from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from chatrooms.apps.chats.schemas import ChatCreate, ChatDetail
from chatrooms.apps.chats.models import Chat
from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User
from starlette.status import (
    HTTP_201_CREATED, HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
)
from tortoise.exceptions import DoesNotExist


chats_router = APIRouter()


@chats_router.post('/', status_code=HTTP_201_CREATED, response_model=ChatDetail)
async def create_chat(chat_data: ChatCreate, user: User = Depends(get_current_user)):
    is_title_taken = await Chat.filter(creator=user, title=chat_data.title).exists()
    if is_title_taken:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='You already created chat with the title.')

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
    return None
