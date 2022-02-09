import pytest
from tortoise.contrib.test import finalizer, initializer
from httpx import AsyncClient

from chatrooms.apps.users.models import User
from chatrooms.apps.users.security import get_password_hash
from chatrooms.config import settings
from main import app


@pytest.fixture(autouse=True)
def fake_db(request):
    initializer(db_url="sqlite://:memory:", modules=settings.APPS_MODELS)
    request.addfinalizer(finalizer)


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def user():
    return await User.create(
        email="testuser@example.com",
        password=get_password_hash('password1'),
    )
