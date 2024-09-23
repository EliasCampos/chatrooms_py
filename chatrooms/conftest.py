import pytest
import asyncio
from tortoise.contrib.test import finalizer, initializer
from httpx import AsyncClient
from pydantic import PostgresDsn, parse_obj_as

from chatrooms.apps.common.mail import fast_mail
from chatrooms.apps.users.tests.factories import UserFactory
from chatrooms.config import settings
from main import app


def pytest_configure(config):
    fast_mail.config.SUPPRESS_SEND = 1


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(autouse=True)
def fake_db(event_loop):
    base_url = parse_obj_as(PostgresDsn, settings.DATABASE_URI)
    fake_url = PostgresDsn.build(
        scheme=base_url.scheme,
        host=base_url.host,
        port=base_url.port,
        path=f'{base_url.path}_TEST',
        user=base_url.user,
        password=base_url.password,
    )
    initializer(db_url=fake_url, modules=settings.APPS_MODELS, loop=event_loop)
    yield
    finalizer()


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def user():
    return await UserFactory()
