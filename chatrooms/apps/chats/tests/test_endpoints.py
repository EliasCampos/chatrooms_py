import json
from uuid import uuid4

from fastapi import status
import websockets

from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.chats.tests.factories import ChatFactory
from chatrooms.apps.users.models import Token
from chatrooms.apps.users.tests.factories import UserFactory
from chatrooms.apps.users.tests.utils import authenticate


async def test_create_chat(async_client, user):
    payload = {
        "title": "test_chat",
    }

    await authenticate(async_client, user)
    response = await async_client.post(f'/api/v1/chats/', json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    assert await Chat.filter(title="test_chat", creator=user).exists()
    chat = await Chat.get(title="test_chat", creator=user)
    data = response.json()
    assert data['id'] == str(chat.id)
    assert data['title'] == str(chat.title)
    assert data['created_at'] == chat.created_at.isoformat()
    assert data['creator']['id'] == user.id
    assert data['creator']['email'] == user.email


async def test_create_chat_title_exists(async_client, user):
    chat = await ChatFactory()

    payload = {
        "title": chat.title,
    }
    await authenticate(async_client, chat.creator)
    response = await async_client.post(f'/api/v1/chats/', json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data['detail']['title'] == "You already created chat with the title."


async def test_delete_chat(async_client):
    chat = await ChatFactory()

    await authenticate(async_client, chat.creator)
    response = await async_client.delete(f'/api/v1/chats/{chat.id}')
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert not await Chat.filter(id=chat.id).exists()


async def test_delete_chat_not_own_chat(async_client, user):
    chat = await ChatFactory()

    await authenticate(async_client, user)
    response = await async_client.delete(f'/api/v1/chats/{chat.id}')
    assert response.status_code == status.HTTP_403_FORBIDDEN

    data = response.json()
    assert data['detail'] == "Can't delete not own chat"


async def test_delete_chat_does_not_exist(async_client, user):
    await authenticate(async_client, user)
    response = await async_client.delete(f'/api/v1/chats/{uuid4()}')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert data['detail'] == "Chat not found."


async def test_send_chat_messages(live_server, user):
    chat = await Chat.create(title="test", creator=user)
    await Token.create(user=user, key="111")
    other_user = await UserFactory()
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
