from nasdaq_protocols.common import *
from nasdaq_protocols import itch

from .soup_client_app_tests import soup_clientapp_common_tests


class TestOrderBookMessage(itch.Message, indicator=1):
    __test__ = False
    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
            Field('orderBookId', IntBE),
        ]

    @staticmethod
    def get(key):
        msg = TestOrderBookMessage()
        msg.orderToken = key
        msg.orderBookId = key
        return msg


async def test__soup_clientapp_common_tests__all_basic_tests_pass(soup_clientapp_common_tests):
    await soup_clientapp_common_tests(
        itch.connect_async,
        itch.ClientSession,
        TestOrderBookMessage.get,
    )