import json
from uuid import uuid4

from fastapi import status
import websockets

from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.chats.tests.factories import ChatFactory, ChatMessageFactory
from chatrooms.apps.users.models import Token
from chatrooms.apps.users.tests.factories import UserFactory
from chatrooms.apps.users.tests.utils import authenticate


async def test_create_chat(async_client, user):
    payload = {
        "title": "test_chat",
    }

    await authenticate(async_client, user)
    response = await async_client.post('/api/v1/chats/', json=payload)
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
    response = await async_client.post('/api/v1/chats/', json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data['title'] == "You already created chat with the title."


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


async def test_list_own_chats(async_client, user):
    chat2 = await ChatFactory(creator=user)
    chat1 = await ChatFactory(creator=user)

    await authenticate(async_client, user)
    response = await async_client.get('/api/v1/chats/own')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['count'] == 2
    assert data['previous'] is None
    assert data['next'] is None
    results = data['results']
    assert results[0]['id'] == str(chat1.id)
    assert results[1]['id'] == str(chat2.id)

    assert results[0]['title'] == chat1.title
    assert results[0]['created_at'] == chat1.created_at.isoformat()


async def test_join_chat(async_client, user):
    chat = await ChatFactory()

    await authenticate(async_client, user)
    response = await async_client.post(f'/api/v1/chats/{chat.id}/access')
    assert response.status_code == status.HTTP_200_OK
    assert await chat.participants.filter(id=user.id).exists()
    data = response.json()
    assert data['detail'] == 'Joined'


async def test_list_joined_chats(async_client, user):
    chat2 = await ChatFactory(title='B')
    await chat2.participants.add(user)
    chat1 = await ChatFactory(title='A')
    await chat1.participants.add(user)

    await authenticate(async_client, user)
    response = await async_client.get('/api/v1/chats/joined')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    results = data['results']
    assert results[0]['id'] == str(chat1.id)
    assert results[1]['id'] == str(chat2.id)

    assert results[0]['title'] == chat1.title
    assert results[0]['created_at'] == chat1.created_at.isoformat()
    assert results[0]['creator']['id'] == chat1.creator_id
    assert results[0]['creator']['email'] == chat1.creator.email


async def test_retrieve_chat_details_own_chat(async_client, user):
    chat = await ChatFactory(creator=user)

    await authenticate(async_client, user)
    response = await async_client.get(f'/api/v1/chats/{chat.id}')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['id'] == str(chat.id)
    assert data['title'] == chat.title
    assert data['created_at'] == chat.created_at.isoformat()
    assert data['creator']['id'] == user.id
    assert data['creator']['email'] == user.email


async def test_retrieve_chat_details_joined_chat(async_client, user):
    chat = await ChatFactory()
    await chat.participants.add(user)

    await authenticate(async_client, user)
    response = await async_client.get(f'/api/v1/chats/{chat.id}')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['id'] == str(chat.id)
    assert data['title'] == chat.title
    assert data['created_at'] == chat.created_at.isoformat()
    assert data['creator']['id'] == chat.creator_id
    assert data['creator']['email'] == chat.creator.email


async def test_send_chat_messages(live_server, user):
    chat = await ChatFactory(creator=user)
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


async def test_list_chat_messages(async_client, user):
    chat = await ChatFactory()
    await chat.participants.add(user)

    msg3, msg2, msg1 = await ChatMessageFactory.create_batch(size=3, chat=chat)

    await authenticate(async_client, user)
    response = await async_client.get(f'/api/v1/chats/{chat.id}/messages')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    results = data['results']
    assert len(results) == 3
    assert results[0]['id'] == msg1.id
    assert results[1]['id'] == msg2.id
    assert results[2]['id'] == msg3.id

    assert results[0]['text'] == msg1.text
    assert results[0]['created_at'] == msg1.created_at.isoformat()
    assert not results[0]['is_deleted']
    assert results[0]['author']['id'] == msg1.author_id
    assert results[0]['author']['email'] == msg1.author.email


async def test_delete_chat_message(async_client, user):
    chat = await ChatFactory()
    await chat.participants.add(user)

    message = await ChatMessageFactory(chat=chat, author=user)

    await authenticate(async_client, user)
    response = await async_client.delete(f'/api/v1/chats/{chat.id}/messages/{message.id}')
    assert response.status_code == status.HTTP_204_NO_CONTENT

    await message.refresh_from_db()
    assert message.text == ''
    assert message.is_deleted


async def test_delete_chat_message_not_own_message(async_client, user):
    chat = await ChatFactory()
    await chat.participants.add(user)

    message = await ChatMessageFactory(chat=chat)

    await authenticate(async_client, user)
    response = await async_client.delete(f'/api/v1/chats/{chat.id}/messages/{message.id}')
    assert response.status_code == status.HTTP_403_FORBIDDEN

    await message.refresh_from_db()
    assert not message.is_deleted

    data = response.json()
    assert data['detail'] == "Can't delete not own chat"
