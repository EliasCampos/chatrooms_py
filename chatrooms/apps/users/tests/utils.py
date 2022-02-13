from httpx import AsyncClient

from chatrooms.apps.users.models import User, Token


async def authenticate(async_client: AsyncClient, user: User):
    token = await Token.generate(user)
    async_client.headers['Authorization'] = f'Token {token.key}'
