from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi_mail import MessageSchema

from chatrooms.apps.common.mail import fast_mail
from chatrooms.apps.common.schemas import ResponseDetail
from chatrooms.apps.users import services as user_services
from chatrooms.apps.users.authentication import get_current_user
from chatrooms.apps.users.models import User
from chatrooms.apps.users.schemas import UserRegister, UserLogin, TokenResult, PasswordReset, PasswordResetConfirm


auth_router = APIRouter()


@auth_router.post('/register', response_model=TokenResult, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    token = await user_services.register_user(user_data)
    return TokenResult.from_orm(token)


@auth_router.post('/login', response_model=TokenResult)
async def login_user(user_data: UserLogin):
    token = await user_services.login_user(user_data)
    return TokenResult.from_orm(token)


@auth_router.post('/logout', response_model=ResponseDetail)
async def logout_user(user: User = Depends(get_current_user)):
    await user_services.logout_user(user)
    return {'detail': "Logged out"}


@auth_router.post('/password/reset', response_model=ResponseDetail)
async def reset_password(password_reset: PasswordReset, background_tasks: BackgroundTasks):
    reset_creds = await user_services.reset_password(email=password_reset.email)
    if reset_creds:
        message = MessageSchema(
            subject="Password Reset on ChatRooms",
            recipients=[password_reset.email],
            template_body=reset_creds.dict(),
        )
        background_tasks.add_task(fast_mail.send_message, message, template_name="password_reset.html")
    return {'detail': "Password reset e-mail has been sent."}


@auth_router.post('/password/reset/confirm', response_model=ResponseDetail)
async def reset_password_confirm(password_reset_confirm: PasswordResetConfirm):
    await user_services.confirm_password_reset(confirm=password_reset_confirm)
    return {'detail': "Password has been reset with the new password."}
