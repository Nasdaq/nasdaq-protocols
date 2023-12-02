import inspect
import logging

from functools import wraps

__all__ = [
    'logable'
]


def logable(target):
    """decorator to add a logger to a class"""
    assert inspect.isclass(target)

    target.log = logging.getLogger(target.__name__)
    return target
