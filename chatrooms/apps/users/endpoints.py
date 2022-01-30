from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from tortoise.exceptions import DoesNotExist

from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.schemas import UserRegister, UserLogin, TokenResult, LogoutResult
from chatrooms.apps.users.security import get_password_hash


auth_router = APIRouter()


@auth_router.post('/register', response_model=TokenResult, status_code=HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    is_user_exists = await User.all().filter(email=user_data.email).exists()
    if is_user_exists:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail={'email': "User with the email already exists."})

    password_hash = get_password_hash(user_data.password)
    user = await User.create(**user_data.dict(exclude={'password'}), password=password_hash)
    token = await Token.generate(user)
    return TokenResult.from_orm(token)


@auth_router.post('/login', response_model=TokenResult)
async def login_user(user_data: UserLogin):
    error_message = {'non_field_errors': "Invalid email or password."}

    try:
        user = await User.get(email=user_data.email)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error_message)

    if not user.check_password(password=user_data.password):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error_message)

    try:
        token = await Token.all().select_related('user').get(user=user)
    except DoesNotExist:
        token = await Token.generate(user)

    return TokenResult.from_orm(token)


@auth_router.post('/logout', response_model=LogoutResult)
async def logout_user(user: User = Depends(get_current_user)):
    await Token.filter(user=user).delete()
    return {'detail': "Logged out"}
