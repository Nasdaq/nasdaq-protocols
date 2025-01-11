from nasdaq_protocols.common import *
from nasdaq_protocols import sqf


@logable
class App1SqfMessage(sqf.Message, app_name='sqf_app_1'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App1SqfMessage')

        kwargs['app_name'] = 'sqf_app_1'
        super().__init_subclass__(**kwargs)


@logable
class App2SqfMessage(sqf.Message, app_name='sqf_app_2'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App2SqfMessage')

        kwargs['app_name'] = 'sqf_app_2'
        super().__init_subclass__(**kwargs)


class TestSqfApp1Message1Out(App1SqfMessage, direction='outgoing', indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
        ]

    @staticmethod
    def get(key):
        msg = TestSqfApp1Message1Out()
        msg.orderToken = key
        return msg


class TestSqfApp1Message2Out(App1SqfMessage, direction='outgoing', indicator=2):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', CharAscii),
        ]

    @staticmethod
    def get(key):
        msg = TestSqfApp1Message2Out()
        msg.orderToken = key
        return msg


class TestSqfApp1MessageIn(App1SqfMessage, direction='incoming', indicator=3):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
        ]

    @staticmethod
    def get(key):
        msg = TestSqfApp1MessageIn()
        msg.orderToken = key
        return msg


class TestSqfApp2MessageOut(App2SqfMessage, direction='outgoing', indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', FixedAsciiString(2)),
        ]

    @staticmethod
    def get(key):
        msg = TestSqfApp2MessageOut()
        msg.orderToken = key
        return msg


def test__from_bytes__different_indicator__decodes_correct_message():
    app1_msg1_out = TestSqfApp1Message1Out.get(123456789)
    app1_msg2_out = TestSqfApp1Message2Out.get('c')

    decoded_app1_msg1_out = App1SqfMessage.from_bytes(app1_msg1_out.to_bytes()[1])
    assert decoded_app1_msg1_out[1] == app1_msg1_out

    decoded_app1_msg2_out = App1SqfMessage.from_bytes(app1_msg2_out.to_bytes()[1])
    assert decoded_app1_msg2_out[1] == app1_msg2_out


def test__from_bytes__same_identifier_different_apps_returns_correct_message():
    app1_msg = TestSqfApp1Message1Out.get(123456789)
    app2_msg = TestSqfApp2MessageOut.get('AB')

    decoded_app1_msg = App1SqfMessage.from_bytes(app1_msg.to_bytes()[1])
    assert decoded_app1_msg[1] == app1_msg

    decoded_app2_msg = App2SqfMessage.from_bytes(app2_msg.to_bytes()[1])
    assert decoded_app2_msg[1] == app2_msg