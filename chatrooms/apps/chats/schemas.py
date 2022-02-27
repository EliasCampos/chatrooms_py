from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, constr


class ChatCreate(BaseModel):
    title: constr(min_length=1, max_length=160, strip_whitespace=True)


class ChatCreator(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


class ChatDetail(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    creator: ChatCreator

    class Config:
        orm_mode = True


class ChatOwn(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        orm_mode = True


class ChatMessageCreate(BaseModel):
    text: constr(min_length=1, max_length=500, strip_whitespace=True)


class ChatMessageAuthor(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


class ChatMessageDetail(BaseModel):
    id: int
    text: str
    created_at: datetime
    is_deleted: bool
    author: ChatMessageAuthor

    class Config:
        orm_mode = True
