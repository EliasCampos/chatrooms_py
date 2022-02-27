import hashlib
import hmac
import time
from typing import Optional

from tortoise.exceptions import DoesNotExist

from chatrooms.apps.common.exceptions import BadInputError
from chatrooms.apps.common.utils import base36_to_int, int_to_base36
from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.schemas import UserRegister, UserLogin, PasswordResetCredentials, PasswordResetConfirm
from chatrooms.apps.users.security import get_password_hash
from chatrooms.config import settings


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


class PasswordResetTokenGenerator:
    secret: str

    SALT: str = 'password_reset_token'
    TIMEOUT = 60 * 60 * 24  # 1 day

    def __init__(self):
        self.secret = settings.SECRET_KEY

    def make_token(self, user: User):
        return self._make_token_with_timestamp(user, timestamp=self._now_seconds())

    def check_token(self, user: User, token: str):
        try:
            timestamp_b36, __ = token.split("-")
        except ValueError:
            return False

        try:
            timestamp = base36_to_int(timestamp_b36)
        except ValueError:
            return False

        return (self._make_token_with_timestamp(user, timestamp) == token
                and self._now_seconds() - timestamp <= self.TIMEOUT)

    def _make_token_with_timestamp(self, user: User, timestamp: int) -> str:
        hash_value = f'{user.pk}{user.email}{timestamp}'

        key_salt = self.SALT.encode()
        secret = self.secret.encode()

        key = hashlib.sha256(key_salt + secret).digest()
        hashed = hmac.new(key, msg=hash_value.encode(), digestmod=hashlib.sha256).hexdigest()

        timestamp_b36 = int_to_base36(timestamp)
        return f'{timestamp_b36}-{hashed}'

    @staticmethod
    def _now_seconds() -> int:
        return int(time.time())


async def reset_password(email: str) -> Optional[PasswordResetCredentials]:
    try:
        user = await User.get(email=email)
    except DoesNotExist:
        return None

    reset_token = PasswordResetTokenGenerator().make_token(user)
    uuid = int_to_base36(user.pk)
    return PasswordResetCredentials(token=reset_token, uuid=uuid)


async def _get_user_from_uuid36(uuid: str) -> User:
    error_message = 'Bad uuid'

    try:
        pk = base36_to_int(uuid)
    except ValueError:
        raise BadInputError({'uuid': error_message})

    try:
        return await User.get(id=pk)
    except DoesNotExist:
        raise BadInputError({'uuid': error_message})


async def confirm_password_reset(confirm: PasswordResetConfirm):
    user = await _get_user_from_uuid36(confirm.uuid)
    if not PasswordResetTokenGenerator().check_token(user, token=confirm.token):
        raise BadInputError({'token': 'Invalid or expired token'})

    password_hash = get_password_hash(confirm.new_password)
    user.password = password_hash
    await user.save(update_fields=['password'])
