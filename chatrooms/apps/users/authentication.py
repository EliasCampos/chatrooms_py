from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from tortoise.exceptions import DoesNotExist

from chatrooms.apps.users.models import Token, User


authorization_header = APIKeyHeader(name='Authorization')


async def get_current_user(authorization: str = Security(authorization_header)) -> User:
    token_key = extract_token_from_header(authorization)
    try:
        token = await Token.all().select_related('user').get(key=token_key)
    except DoesNotExist:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token header.')

    return token.user


def extract_token_from_header(authorization: str) -> str:
    auth = authorization.split()

    if not auth or auth[0].lower() != 'token' or len(auth) == 1 or len(auth) > 2:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token header.')

    token = auth[1]
    return token
