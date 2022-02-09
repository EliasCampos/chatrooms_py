import json

import websockets

from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.users.models import User, Token


async def test_send_chat_messages(live_server, user):
    chat = await Chat.create(title="test", creator=user)
    await Token.create(user=user, key="111")
    other_user = await User.create(email="foo@bar.com", password='123')
    await chat.participants.add(other_user)
    await Token.create(user=other_user, key="222")

    url = f'ws://{live_server.netloc}/api/v1/chats/ws/{chat.id}'
    async with websockets.connect(f'{url}?token=111') as ws1, websockets.connect(f'{url}?token=222') as ws2:
        await ws1.send("test text")
        result1_1 = await ws1.recv()
        result1_2 = await ws2.recv()
        assert result1_1.startswith('new_message:')
        assert result1_1 == result1_2

        data1 = json.loads(result1_2.lstrip('new_message:'))
        assert data1['text'] == "test text"

        await ws1.send("")
        result = await ws1.recv()
        assert result.startswith('validation_error:')

        await ws2.send("other test text")
        result2_1 = await ws1.recv()
        result2_2 = await ws2.recv()
        assert result2_1.startswith('new_message:')
        assert result2_1 == result2_2

        data2 = json.loads(result2_2.lstrip('new_message:'))
        assert data2['text'] == "other test text"

    assert await ChatMessage.filter(chat=chat, author=user, text="test text").count() == 1
    message1 = await ChatMessage.get(chat=chat, author=user, text="test text")
    assert data1['id'] == message1.id
    assert data1['created_at'] == message1.created_at.isoformat()
    assert not data1['is_deleted']

    assert await ChatMessage.filter(chat=chat, author=other_user, text="other test text").count() == 1
    message2 = await ChatMessage.get(chat=chat, author=other_user, text="other test text")
    assert data2['id'] == message2.id
    assert data2['created_at'] == message2.created_at.isoformat()
    assert not data2['is_deleted']
