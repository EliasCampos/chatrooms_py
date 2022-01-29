from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class ChatCreate(BaseModel):
    title: str


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


class ChatJoinResult(BaseModel):
    detail: str
