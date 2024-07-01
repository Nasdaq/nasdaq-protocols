from nasdaq_protocols.common import *
from nasdaq_protocols import itch


@logable
class App1ItchMessage(itch.Message, app_name='itch_app_1'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App1ItchMessage')

        kwargs['app_name'] = 'itch_app_1'
        super().__init_subclass__(**kwargs)


@logable
class App2ItchMessage(itch.Message, app_name='itch_app_2'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App2ItchMessage')

        kwargs['app_name'] = 'itch_app_2'
        super().__init_subclass__(**kwargs)


class TestItchApp1Message1(App1ItchMessage, indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
        ]

    @staticmethod
    def get(key):
        msg = TestItchApp1Message1()
        msg.orderToken = key
        return msg


class TestItchApp1Message2(App1ItchMessage, indicator=2):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', FixedAsciiString(2)),
        ]

    @staticmethod
    def get(key):
        msg = TestItchApp1Message2()
        msg.orderToken = key
        return msg


class TestItchApp2Message(App2ItchMessage, indicator=1):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('orderToken', CharAscii),
        ]

    @staticmethod
    def get(key):
        msg = TestItchApp2Message()
        msg.orderToken = key
        return msg


def test__from_bytes__different_identifier_same_app__returns_correct_message():
    app1_msg = TestItchApp1Message1.get(123456789)
    app2_msg = TestItchApp1Message2.get('AB')

    decoded_app_1_msg1 = App1ItchMessage.from_bytes(app1_msg.to_bytes()[1])
    assert decoded_app_1_msg1[1] == app1_msg

    decoded_app_1_msg2 = App1ItchMessage.from_bytes(app2_msg.to_bytes()[1])
    assert decoded_app_1_msg2[1] == app2_msg


def test__from_bytes__same_identifier_different_apps__returns_correct_message():
    app1_msg = TestItchApp1Message1.get(123456789)
    app2_msg = TestItchApp2Message.get('B')

    decoded_app_1_msg = App1ItchMessage.from_bytes(app1_msg.to_bytes()[1])
    assert decoded_app_1_msg[1] == app1_msg

    decoded_app_2_msg = App2ItchMessage.from_bytes(app2_msg.to_bytes()[1])
    assert decoded_app_2_msg[1] == app2_msg
