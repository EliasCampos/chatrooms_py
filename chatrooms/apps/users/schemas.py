from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInToken(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


class TokenResult(BaseModel):
    key: str
    user: UserInToken

    class Config:
        orm_mode = True


class LogoutResult(BaseModel):
    detail: str
