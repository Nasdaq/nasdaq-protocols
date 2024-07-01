import asyncio
import logging
from typing import Any, Callable

import attrs
import pytest
from nasdaq_protocols import common
from nasdaq_protocols.common import Serializable


__all__ = [
    'Action',
    'Matcher',
    'ActonExecutor',
    'MockServerSession',
    'matches',
    'send',
]
Action = Callable[['MockServerSession', Any], None]
Matcher = Callable[[Any], bool]
_logger = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class ActonExecutor:
    session: 'MockServerSession'
    name: str = attrs.field(default='default')
    actions: list[tuple[str, Action]] = attrs.field(init=False, factory=list)

    def do(self, action: Action, name: str = 'default') -> 'ActonExecutor':
        self.actions.append((name, action))
        return self

    def __call__(self, data: Any, *args, **kwargs):
        for name, action in self.actions:
            _logger.debug('Executing action : %s', name)
            action(self.session, data)


@attrs.define(auto_attribs=True)
class MockServerSession(asyncio.Protocol):
    connected: bool = attrs.field(init=False, default=False)
    port: int = attrs.field(init=False, default=0)
    actions: list[tuple[Matcher, ActonExecutor]] = attrs.field(init=False, factory=list)
    transport: asyncio.Transport | asyncio.BaseTransport = None

    def connection_made(self, transport):
        self.connected = True
        self.transport = transport

    def data_received(self, data):
        for predicate, executor in self.actions:
            _logger.debug('testing matcher : %s', executor.name)
            if predicate(data):
                _logger.debug('matcher : %s, matched', executor.name)
                executor(data)
            else:
                _logger.debug('matcher : %s, not matched', executor.name)

    def connection_lost(self, exc):
        self.connected = False

    def send(self, data: str | common.Serializable | bytes):
        # send protocols: len + data
        if self.transport:
            if isinstance(data, str):
                data = data.encode('ascii')
            elif isinstance(data, common.Serializable):
                data = data.to_bytes()[1]
            elif isinstance(data, bytes):
                pass
            else:
                raise ValueError(f'Unsupported data type: {type(data)}')
            self.transport.write(data)

    def when(self, matcher: Matcher, name: str = 'default') -> ActonExecutor:
        executor = ActonExecutor(self, name=name)
        self.actions.append((matcher, executor))
        return executor

    def close(self):
        if self.transport:
            self.transport.close()


def matches(serializable: Serializable):
    return lambda actual: serializable.to_bytes()[1] == actual


def send(serializable: Serializable):
    return lambda session, _data: session.send(serializable)

