import asyncio
import logging
from collections import OrderedDict
from typing import Any, Callable

import attrs
import pytest
from nasdaq_protocols import common


Action = Callable[[Any], None]
Matcher = Callable[[Any], bool]
_logger = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class ActonExecutor:
    actions: list[Action] = attrs.field(init=False, factory=list)

    def do(self, action: Action) -> 'ActonExecutor':
        self.actions.append(action)
        return self

    def execute(self, data: Any):
        for action in self.actions:
            action(data)


@attrs.define(auto_attribs=True)
class MockServerSession(asyncio.Protocol):
    connected: bool = attrs.field(init=False, default=False)
    port: int = attrs.field(init=False, default=0)
    actions: dict[Matcher, ActonExecutor] = attrs.field(init=False, factory=OrderedDict)
    transport: asyncio.Transport | asyncio.BaseTransport = None

    def connection_made(self, transport):
        self.connected = True
        self.transport = transport

    def data_received(self, data):
        for predicate, executor in self.actions.items():
            if predicate(data):
                executor.execute(data)

    def connection_lost(self, exc):
        self.connected = False

    def send(self, data: str | common.Serializable | bytes):
        # send protocols: len + data
        if self.transport:
            if isinstance(data, str):
                data = data.encode('ascii')
            elif isinstance(data, common.Serializable):
                data = data.to_bytes()
            elif isinstance(data, bytes):
                pass
            else:
                raise ValueError(f'Unsupported data type: {type(data)}')
            self.transport.write(data)

    def when(self, matcher: Matcher) -> ActonExecutor:
        executor = ActonExecutor()
        self.actions[matcher] = executor
        return executor

    def close(self):
        if self.transport:
            self.transport.close()


@pytest.fixture(scope='function')
async def mock_server_session(unused_tcp_port):
    session = MockServerSession()
    server, serving_task = await common.start_server(('127.0.0.1', unused_tcp_port), lambda: session)
    yield unused_tcp_port, session
    await common.stop_task(serving_task)
