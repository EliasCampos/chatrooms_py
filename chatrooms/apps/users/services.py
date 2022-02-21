from tortoise.exceptions import DoesNotExist

from chatrooms.apps.common.exceptions import BadInputError
from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.schemas import UserRegister, UserLogin
from chatrooms.apps.users.security import get_password_hash


async def register_user(user_data: UserRegister) -> Token:
    is_user_exists = await User.all().filter(email=user_data.email).exists()
    if is_user_exists:
        raise BadInputError({'email': "User with the email already exists."})

    password_hash = get_password_hash(user_data.password)
    user = await User.create(**user_data.dict(exclude={'password'}), password=password_hash)
    token = await Token.generate(user)
    return token


async def login_user(user_data: UserLogin) -> Token:
    error_message = {'non_field_errors': "Invalid email or password."}

    try:
        user = await User.get(email=user_data.email)
    except DoesNotExist:
        raise BadInputError(error_message)

    if not user.check_password(password=user_data.password):
        raise BadInputError(error_message)

    try:
        token = await Token.all().select_related('user').get(user=user)
    except DoesNotExist:
        token = await Token.generate(user)

    return token


async def logout_user(user: User) -> None:
    await Token.filter(user=user).delete()
