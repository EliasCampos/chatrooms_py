import asyncio
from collections import defaultdict
from functools import partial
from typing import Dict, Set, Optional
from uuid import UUID

from fastapi import status, Query, WebSocket
from tortoise.exceptions import DoesNotExist

from chatrooms.apps.users.models import Token


async def get_ws_user(websocket: WebSocket, token: Optional[str] = Query(None)):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        token_obj = await Token.all().select_related('user').get(key=token)
    except DoesNotExist:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    return token_obj.user


class ChatsConnectionManager:
    _chats_users_connections: Dict[UUID, Dict[int, Set[WebSocket]]]

    def __init__(self):
        self._chats_users_connections = defaultdict(partial(defaultdict, set))

    def add_connection(self, chat_id: UUID, user_id: int, connection: WebSocket):
        self._chats_users_connections[chat_id][user_id].add(connection)

    def remove_connection(self, chat_id: UUID, user_id: int, connection: WebSocket):
        self._chats_users_connections[chat_id][user_id].remove(connection)

    async def send_chat_message(self, chat_id: UUID, message: str):
        tasks = [
            connection.send_text(message)
            for user_connections in self._chats_users_connections[chat_id].values()
            for connection in user_connections
        ]
        await asyncio.gather(*tasks)


chats_connections = ChatsConnectionManager()