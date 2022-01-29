from fastapi import APIRouter, HTTPException

from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.schemas import UserRegister, TokenResult
from chatrooms.apps.users.security import get_password_hash

auth_router = APIRouter()


@auth_router.post('/register', response_model=TokenResult)
async def register_user(user_data: UserRegister):
    is_user_exists = await User.all().filter(email=user_data.email).exists()
    if is_user_exists:
        raise HTTPException(status_code=400, detail="User with the email already exists.")

    password_hash = get_password_hash(user_data.password)
    user = await User.create(**user_data.dict(exclude={'password'}), password=password_hash)
    token = await Token.generate(user)
    return TokenResult.from_orm(token)
