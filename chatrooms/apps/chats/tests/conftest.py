import pytest

import asyncio
from dataclasses import dataclass, field
from typing import Optional

import uvicorn

from main import app


@dataclass
class LiveServer:
    host: str
    port: int
    _server: uvicorn.Server = field(init=False, repr=False)
    _task: Optional[asyncio.Task] = field(init=False, repr=False)

    def __post_init__(self):
        self._server = uvicorn.Server(config=uvicorn.Config(app, host=self.host, port=self.port, log_level='error'))
        self._task = None

    async def start(self):
        self._server.config.setup_event_loop()
        self._task = asyncio.create_task(self._server.serve())
        await self.wait_connection()

    async def stop(self):
        self._server.should_exit = True
        await self._task

    async def wait_connection(self):
        while not self._server.started:
            await asyncio.sleep(0.1)

    @property
    def netloc(self) -> str:
        return f'{self.host}:{self.port}'


@pytest.fixture
async def live_server(mocker):
    mocker.patch('tortoise.Tortoise.init')  # mock app startup event to prevent connect of real db
    mocker.patch('tortoise.Tortoise.close_connections')

    server = LiveServer(host="127.0.0.1", port=3003)
    await server.start()
    yield server
    await server.stop()
