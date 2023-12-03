import asyncio
import inspect
import logging

from functools import wraps

__all__ = [
    'logable',
    'stop_task',
    'Validators',
]


def logable(target):
    """decorator to add a logger to a class"""
    assert inspect.isclass(target)

    target.log = logging.getLogger(target.__name__)
    return target


async def stop_task(task: asyncio.Task) -> asyncio.Task | None:
    """Cancel a task and wait for it to finish"""
    if task is None:
        return
    try:
        task.cancel()
        await task
    except asyncio.CancelledError:
        pass
    except RuntimeError:
        pass


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
