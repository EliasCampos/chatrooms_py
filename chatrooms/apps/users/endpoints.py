from fastapi import APIRouter, HTTPException
from tortoise.exceptions import DoesNotExist

from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.schemas import UserRegister, UserLogin, TokenResult
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


@auth_router.post('/login', response_model=TokenResult)
async def login_user(user_data: UserLogin):
    error_message = "Invalid email or password."

    try:
        user = await User.get(email=user_data.email)
    except DoesNotExist:
        raise HTTPException(status_code=400, detail=error_message)

    if not user.check_password(password=user_data.password):
        raise HTTPException(status_code=400, detail=error_message)

    try:
        token = await Token.all().select_related('user').get(user=user)
    except DoesNotExist:
        token = await Token.generate(user)

    return TokenResult.from_orm(token)
