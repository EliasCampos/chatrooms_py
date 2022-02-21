from fastapi import APIRouter, Depends, status

from chatrooms.apps.users import services as user_services
from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User
from chatrooms.apps.users.schemas import UserRegister, UserLogin, TokenResult, LogoutResult


auth_router = APIRouter()


@auth_router.post('/register', response_model=TokenResult, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    token = await user_services.register_user(user_data)
    return TokenResult.from_orm(token)


@auth_router.post('/login', response_model=TokenResult)
async def login_user(user_data: UserLogin):
    token = await user_services.login_user(user_data)
    return TokenResult.from_orm(token)


@auth_router.post('/logout', response_model=LogoutResult)
async def logout_user(user: User = Depends(get_current_user)):
    await user_services.logout_user(user)
    return {'detail': "Logged out"}
