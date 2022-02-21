from fastapi import status

from chatrooms.apps.users.models import User, Token
from chatrooms.apps.users.tests.factories import USER_PASSWORD
from chatrooms.apps.users.tests.utils import authenticate


async def test_register_user(async_client):
    payload = {
        "email": "test@example.com",
        "password": "strongpassword",
    }

    response = await async_client.post('/api/v1/auth/register', json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    assert await User.filter(email="test@example.com").exists()
    user = await User.get(email="test@example.com")
    assert user.check_password("strongpassword")
    assert await Token.filter(user=user).exists()
    token = await Token.get(user=user)

    data = response.json()
    assert data['key'] == token.key
    assert data['user']['id'] == user.id
    assert data['user']['email'] == user.email


async def test_register_user_already_exists(async_client, user):
    payload = {
        "email": user.email,
        "password": "password1",
    }

    response = await async_client.post('/api/v1/auth/register', json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data['email'] == "User with the email already exists."


async def test_login_user(async_client, user):
    payload = {
        "email": user.email,
        "password": USER_PASSWORD,
    }

    response = await async_client.post('/api/v1/auth/login', json=payload)
    assert response.status_code == status.HTTP_200_OK

    assert await Token.filter(user=user).exists()
    token = await Token.get(user=user)

    data = response.json()
    assert data['key'] == token.key
    assert data['user']['id'] == user.id
    assert data['user']['email'] == user.email


async def test_login_user_already_authenticated(async_client, user):
    payload = {
        "email": user.email,
        "password": USER_PASSWORD,
    }

    await authenticate(async_client, user)
    assert await Token.filter(user=user).exists()
    token = await Token.get(user=user)

    response = await async_client.post('/api/v1/auth/login', json=payload)
    assert response.status_code == status.HTTP_200_OK

    assert await Token.filter(user=user).count() == 1
    data = response.json()
    assert data['key'] == token.key
    assert data['user']['id'] == user.id
    assert data['user']['email'] == user.email


async def test_login_user_invalid_email(async_client, user):
    payload = {
        "email": f'not_a_{user.email}',
        "password": USER_PASSWORD,
    }

    response = await async_client.post('/api/v1/auth/login', json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert not await Token.filter(user=user).exists()

    data = response.json()
    assert data['non_field_errors'] == "Invalid email or password."


async def test_login_user_invalid_password(async_client, user):
    payload = {
        "email": user.email,
        "password": f'NOT_A_{USER_PASSWORD}',
    }

    response = await async_client.post('/api/v1/auth/login', json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert not await Token.filter(user=user).exists()

    data = response.json()
    assert data['non_field_errors'] == "Invalid email or password."


async def test_logout_user(async_client, user):
    await authenticate(async_client, user)
    assert await Token.filter(user=user).exists()

    response = await async_client.post('/api/v1/auth/logout')
    assert response.status_code == status.HTTP_200_OK

    assert not await Token.filter(user=user).exists()

    data = response.json()
    assert data['detail'] == "Logged out"
