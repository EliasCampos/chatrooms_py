from pydantic import BaseModel, EmailStr, constr


class UserRegister(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=1)


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


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetCredentials(BaseModel):
    uuid: str
    token: str


class PasswordResetConfirm(BaseModel):
    uuid: constr(min_length=1)
    token: constr(min_length=1)
    new_password: constr(min_length=8, max_length=100)
