import asyncio
import inspect
import logging
from typing import Tuple

from .types import Stoppable


__all__ = [
    'logable',
    'stop_task',
    'start_server',
    'Validators',
    'enable_logging_tools'
]
_StopTaskTypes = asyncio.Task | Stoppable
_logger = logging.getLogger(__name__)


async def _stop_stoppable(task: Stoppable):
    await task.stop()


async def _stop_task(task: asyncio.Task):
    if task is None:
        return
    try:
        task.cancel()
        if asyncio.current_task() != task:
            await task
    except asyncio.CancelledError:
        pass
    except RuntimeError as exc:
        _logger.error('Error stopping task: %s', exc)


def logable(target):
    """
    decorator that adds a log object to the class.
    """
    assert inspect.isclass(target)

    target.log = logging.getLogger(target.__name__)
    return target


async def stop_task(tasks: _StopTaskTypes | list[_StopTaskTypes]) -> asyncio.Task | Stoppable | None:
    """
    Cancel a task and wait for it to finish
    """
    if not isinstance(tasks, list):
        tasks = [tasks]

    for task in tasks:
        if isinstance(task, Stoppable):
            await task.stop()
        elif isinstance(task, asyncio.Task):
            await _stop_task(task)

    return None


async def start_server(remote, session_factory, spin_timeout=0.001, *, name='server:serve', **kwargs)\
        -> Tuple[asyncio.Server, asyncio.Task]:
    """ start a socket server and return the server and the task that runs it """

    loop = asyncio.get_running_loop()
    server = await loop.create_server(session_factory, remote[0], remote[1], start_serving=False, **kwargs)
    task = asyncio.create_task(server.serve_forever(), name=name)

    while not server.is_serving():
        await asyncio.sleep(spin_timeout)

    return server, task


def enable_logging_tools(verbose: int, format_: str = '%(asctime)s> %(levelname)s %(message)s'):
    level = logging.WARN
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(format=format_, level=level, datefmt='%Y-%m-%d %H:%M:%S')


class Validators:
    @staticmethod
    def not_none():
        """Validator to check if the value is not None"""
        return Validators._not_none_validator

    @staticmethod
    def _not_none_validator(_inst, attr, value):
        """Validator to check if the value is not None"""
        if value is None:
            raise ValueError(f'{attr.name} cannot be None')
