import pytest

from nasdaq_protocols import common


def test_unable_to_decorate_function_with_loggable():

    with pytest.raises(AssertionError):
        @common.logable
        def func():
            pass


def test_able_to_decorate_class_with_logable():
    @common.logable
    class A:
        pass

    assert hasattr(A, 'log')
    assert A.log.name == 'A'
