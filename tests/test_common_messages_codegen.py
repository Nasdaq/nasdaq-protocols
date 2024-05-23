import os

import pytest

from nasdaq_protocols.common.message import Generator, Parser
from .testdata import *


EXPECTED_GENERATED_CODE = """
from enum import Enum
from nasdaq_protocols.common.message import *
from nasdaq_protocols import ouch


__all__ = [
    'OuchEnterOrder',
]


# Enums
# Records
# Messages
class OuchEnterOrder(ouch.Message, indicator=79, direction='incoming'):
    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
            Field('orderBookId', IntBE),
            Field('side', CharIso8599),
            Field('quantity', LongBE),
            Field('price', LongBE),
            Field('timeInForce', Byte),
            Field('openClose', Byte),
            Field('clientAccount', FixedIsoString(length=16)),
            Field('customerInfo', FixedIsoString(length=15)),
            Field('exchangeInfo', FixedIsoString(length=32)),
            Field('displayQuantity', LongBE),
            Field('orderType', Byte),
            Field('timeInForceData', ShortBE),
            Field('orderCapacity', Byte),
            Field('selfMatchPreventionKey', IntBE),
            Field('attributes', ShortBE),
        ]

    orderToken: int
    orderBookId: int
    side: str
    quantity: int
    price: int
    timeInForce: int
    openClose: int
    clientAccount: str
    customerInfo: str
    exchangeInfo: str
    displayQuantity: int
    orderType: int
    timeInForceData: int
    orderCapacity: int
    selfMatchPreventionKey: int
    attributes: int
"""
EXPECTED_GENERATED_INIT_CODE = """
from .test_ouch_messages import *
"""


@pytest.fixture(scope='function')
def generate_ouch_messages(tmp_file_writer, tmp_path):
    def generator(xml_content, generate_init_file=False):
        generator = Generator(
            Parser.parse(tmp_file_writer(xml_content)),
            'ouch',
            os.path.join(tmp_path, 'output'),
            'test',
            'test.ouch',
            template='message_ouch_itch',
            generate_init_file=generate_init_file
        )
        return generator.generate(extra_context={'record_type': 'Record'})
    return generator


def test__codegen__ouch_message__generate(generate_ouch_messages):
    files = generate_ouch_messages(TEST_XML_OUCH_MESSAGE)
    assert len(files) == 1

    with open(files[0]) as f:
        assert f.read().strip() == EXPECTED_GENERATED_CODE.strip()


def test__codegen__ouch_message__generate_init_file(generate_ouch_messages):
    files = generate_ouch_messages(TEST_XML_OUCH_MESSAGE, generate_init_file=True)
    assert len(files) == 2

    with open(files[1]) as f:
        assert f.read().strip() == EXPECTED_GENERATED_INIT_CODE.strip()