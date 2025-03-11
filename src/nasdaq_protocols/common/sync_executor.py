import asyncio
import concurrent
import threading
from asyncio import iscoroutine

import attrs
from .utils import logable
from .types import StateError


__all__ = ['SyncExecutor']


@attrs.define
@logable
class SyncExecutor:
    """
    A helper class to execute async functions synchronously.

    NOTE: This is experimental and should be used with caution.
    """
    name: str = attrs.field()
    _event_loop: asyncio.BaseEventLoop = attrs.field(init=False)
    _thread: threading.Thread = attrs.field(init=False)

    @staticmethod
    def _work(event_loop):
        asyncio.set_event_loop(event_loop)
        event_loop.run_forever()

    def __attrs_post_init__(self):
        self._event_loop = asyncio.new_event_loop()
        self._thread = threading.Thread(name=f'sync-executor-{self.name}', target=SyncExecutor._work, args=(self._event_loop,))
        self._thread.start()
        self.log.info(f'SyncExecutor[{self.name}] started, thread: {self._thread.ident}')

    def execute(self, underlying, timeout=None):
        """
        Execute an async function synchronously.
        """
        self._must_be_active()

        if not iscoroutine(underlying):
            raise ValueError(f'Expected an async function, got: {underlying}')

        future = asyncio.run_coroutine_threadsafe(underlying, self._event_loop)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise asyncio.TimeoutError(f'Timed out after {timeout} seconds')

    def execute_sync(self, underlying, *args, **kwargs):
        """
        Execute an underlying synchronous function in this context.

        This method wraps the underlying function in a coroutine and executes it synchronously.
        In this way, if the underlying function is creating tasks, they will do so in the same
        event loop.
        """
        self._must_be_active()

        if not callable(underlying):
            raise ValueError(f'Expected a callable, got: {underlying}')

        return self.execute(
            self._bridge(underlying, *args, **kwargs)
        )

    def stop(self, join=True):
        """
        Stop the SyncExecutor and the underlying event loop
        """
        self.log.info(f'Stopping SyncExecutor[{self.name}]')
        self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        if join:
            self._thread.join()

    def join(self):
        """
        Join the underlying thread
        """
        self._thread.join()

    async def _bridge(self, underlying, *args, **kwargs):
        return underlying(*args, **kwargs)

    def _must_be_active(self):
        if not self._thread.is_alive():
            raise StateError(f'SyncExecutor[{self.name}] is not active')
