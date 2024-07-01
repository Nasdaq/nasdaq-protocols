from nasdaq_protocols.common import *
from nasdaq_protocols import ouch


@logable
class App1OuchMessage(ouch.Message, app_name='ouch_app_1'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App1OuchMessage')

        kwargs['app_name'] = 'ouch_app_1'
        super().__init_subclass__(**kwargs)


@logable
class App2OuchMessage(ouch.Message, app_name='ouch_app_2'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App2OuchMessage')

        kwargs['app_name'] = 'ouch_app_2'
        super().__init_subclass__(**kwargs)


class TestOuchApp1Message1Out(App1OuchMessage, direction='outgoing', indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
        ]

    @staticmethod
    def get(key):
        msg = TestOuchApp1Message1Out()
        msg.orderToken = key
        return msg


class TestOuchApp1Message2Out(App1OuchMessage, direction='outgoing', indicator=2):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', CharAscii),
        ]

    @staticmethod
    def get(key):
        msg = TestOuchApp1Message2Out()
        msg.orderToken = key
        return msg


class TestOuchApp1MessageIn(App1OuchMessage, direction='incoming', indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
        ]

    @staticmethod
    def get(key):
        msg = TestOuchApp1MessageIn()
        msg.orderToken = key
        return msg


class TestOuchApp2MessageOut(App2OuchMessage, direction='outgoing', indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', FixedAsciiString(2)),
        ]

    @staticmethod
    def get(key):
        msg = TestOuchApp2MessageOut()
        msg.orderToken = key
        return msg


def test__from_bytes__same_indicator__always_decodes_only_outgoing_message():
    # When same indicator is used for both incoming and outgoing,
    # from client side we always want to decode from_bytes what
    # the server is sending us...
    # so messages marked as "outgoing" should be decoded.
    app1_msg_out = TestOuchApp1Message1Out.get(123456789)

    decoded = App1OuchMessage.from_bytes(app1_msg_out.to_bytes()[1])
    assert isinstance(decoded[1], TestOuchApp1Message1Out)


def test__from_bytes__different_indicator__decodes_correct_message():
    app1_msg1_out = TestOuchApp1Message1Out.get(123456789)
    app1_msg2_out = TestOuchApp1Message2Out.get('c')

    decoded_app1_msg1_out = App1OuchMessage.from_bytes(app1_msg1_out.to_bytes()[1])
    assert decoded_app1_msg1_out[1] == app1_msg1_out

    decoded_app1_msg2_out = App1OuchMessage.from_bytes(app1_msg2_out.to_bytes()[1])
    assert decoded_app1_msg2_out[1] == app1_msg2_out


def test__from_bytes__same_identifier_different_apps_returns_correct_message():
    app1_msg = TestOuchApp1Message1Out.get(123456789)
    app2_msg = TestOuchApp2MessageOut.get('AB')

    decoded_app1_msg = App1OuchMessage.from_bytes(app1_msg.to_bytes()[1])
    assert decoded_app1_msg[1] == app1_msg

    decoded_app2_msg = App2OuchMessage.from_bytes(app2_msg.to_bytes()[1])
    assert decoded_app2_msg[1] == app2_msg