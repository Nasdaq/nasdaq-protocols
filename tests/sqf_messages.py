import asyncio
import time
import logging
from typing import Callable, Awaitable, Type

from nasdaq_protocols.common import *
from nasdaq_protocols import sqf, soup


LOG = logging.getLogger(__name__)


@logable
class App1SqfMessage(sqf.Message, app_name='sqf_app_1'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing App1SqfMessage')

        kwargs['app_name'] = 'sqf_app_1'
        super().__init_subclass__(**kwargs)


class ClientSession(sqf.ClientSession):
    @classmethod
    def decode(cls, bytes_: bytes) -> [int, App1SqfMessage]:
        return App1SqfMessage.from_bytes(bytes_)


async def connect_async(remote: tuple[str, int], user: str, passwd: str, session_id,
                        sequence: int = 0,
                        session_factory: Callable[[soup.SoupClientSession], ClientSession] = None,
                        on_msg_coro: Callable[[Type[App1SqfMessage]], Awaitable[None]] = None,
                        on_close_coro: Callable[[], Awaitable[None]] = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10) -> ClientSession:
    if session_factory is None:
        def session_factory(x):
            return ClientSession(x, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)

    return await sqf.connect_async(
        remote, user, passwd, session_id, sequence,
        session_factory, on_msg_coro, on_close_coro,
        client_heartbeat_interval, server_heartbeat_interval
    )


class SqfQuote(Record):
    Fields = [
        Field('orderBookId', IntBE),
        Field('bidPrice', LongBE),
        Field('askPrice', LongBE),
        Field('bidQuantity', LongBE),
        Field('askQuantity', LongBE),
    ]

    orderBookId: int
    bidPrice: int
    askPrice: int
    bidQuantity: int
    askQuantity: int


class MlQuote(Record):
    Fields = [
        Field('bidPrice', LongBE),
        Field('askPrice', LongBE),
        Field('bidQuantity', LongBE),
        Field('askQuantity', LongBE),
    ]

    bidPrice: int
    askPrice: int
    bidQuantity: int
    askQuantity: int


class SqfQuoteReply(Record):
    Fields = [
        Field('statusCode', IntBE),
    ]

    statusCode: int


class MlQuoteReply(Record):
    Fields = [
        Field('buyOrderId', LongBE),
        Field('sellOrderId', LongBE),
        Field('statusCode', IntBE),
    ]


class SqfQuoteBlockMessage(App1SqfMessage, direction='incoming', indicator=81):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('quoteMessageId', LongBE),
            Field('timestamp', LongBE),
            Field('clientInfo', FixedAsciiString(16)),
            Field('exchangeInfo', FixedAsciiString(32)),
            Field('quotes', Array(SqfQuote, length_type=ShortBE)),
        ]

    quoteMessageId: int
    timestamp: int
    clientInfo: str
    exchangeInfo: str
    quotes: list[SqfQuote]

    @staticmethod
    def get(quotes):
        quotes_ = []
        for quote in quotes:
            quote_ = SqfQuote()
            quote_.orderBookId = quote['orderBookId']
            quote_.bidPrice = quote['bidPrice']
            quote_.askPrice = quote['askPrice']
            quote_.bidQuantity = quote['bidQuantity']
            quote_.askQuantity = quote['askQuantity']
            quotes_.append(quote_)

        id_ = time.time_ns()
        msg = SqfQuoteBlockMessage()
        msg.quoteMessageId = id_
        msg.timestamp = id_
        msg.quotes = quotes_
        return msg


class SqlMlQuoteMessage(App1SqfMessage, direction='incoming', indicator=85):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('quoteMessageId', LongBE),
            Field('timestamp', LongBE),
            Field('clientInfo', FixedAsciiString(16)),
            Field('exchangeInfo', FixedAsciiString(32)),
            Field('orderBookId', IntBE),
            Field('quotes', Array(MlQuote, length_type=ShortBE)),
        ]

    quoteMessageId: int
    timestamp: int
    clientInfo: str
    exchangeInfo: str
    orderBookId: int
    quotes: list[MlQuote]

    @staticmethod
    def get(orderbook_id, quotes):
        quotes_ = []
        for quote in quotes:
            quote_ = MlQuote()
            quote_.bidPrice = quote['bidPrice']
            quote_.askPrice = quote['askPrice']
            quote_.bidQuantity = quote['bidQuantity']
            quote_.askQuantity = quote['askQuantity']
            quotes_.append(quote_)

        msg = SqlMlQuoteMessage()
        id_ = time.time_ns()
        msg.quoteMessageId = id_
        msg.orderBookId = orderbook_id
        msg.timestamp = id_
        msg.quotes = quotes_
        return msg


class SqfOrderBookDirectoryMessage(App1SqfMessage, direction="outgoing", indicator=82):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('seconds', IntBE),
            Field('nanoseconds', IntBE),
            Field('orderBookId', IntBE),
            Field('symbol', FixedAsciiString(32)),
            Field('longName', FixedAsciiString(64)),
            Field('ISIN', FixedAsciiString(12)),
            Field('financialProduct', Byte),
            Field('currency', FixedAsciiString(3)),
            Field('decimalInPrice', ShortBE),
            Field('decimalInNV', ShortBE),
            Field('roundLotSize', IntBE),
            Field('nominalValue', LongBE),
            Field('numberOfLegs', Byte),
            Field('underlying', IntBE),
            Field('strikePrice', IntBE),
            Field('expirationDate', IntBE),
            Field('decimalsInStrikePrice', ShortBE),
            Field('optionType', Byte),
            Field('decimalsInQuantity', ShortBE),
            Field('testOrderbook', Byte),
        ]


class SqfTickSizeTableMessage(App1SqfMessage, direction="outgoing", indicator=76):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('seconds', IntBE),
            Field('nanoseconds', IntBE),
            Field('orderBookId', IntBE),
            Field('tickSize', LongBE),
            Field('priceFrom', LongBE),
            Field('priceTo', LongBE),
        ]


class SqfOrderBookStateMessage(App1SqfMessage, direction="outgoing", indicator=79):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('seconds', IntBE),
            Field('nanoseconds', IntBE),
            Field('orderBookId', IntBE),
            Field('state', FixedAsciiString(20)),
        ]


class SqfCombinationOrderbookLegMessage(App1SqfMessage, direction="outgoing", indicator=77):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('seconds', IntBE),
            Field('nanoseconds', IntBE),
            Field('orderBookId', IntBE),
            Field('legOrderBookId', IntBE),
            Field('legSide', CharAscii),
            Field('legRatio', IntBE)
        ]


class SqfQuoteBlockReplyMessage(App1SqfMessage, direction='outgoing', indicator=113):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('quoteMessageId', LongBE),
            Field('orderId', LongBE),
            Field('timestamp', LongBE),
            Field('responseCode', IntBE),
            Field('clientInfo', FixedAsciiString(16)),
            Field('exchangeInfo', FixedAsciiString(32)),
            Field('quoteCount', ShortBE),
            Field('quoteReplies', Array(SqfQuoteReply, length_type=ShortBE)),
        ]

    quoteMessageId: int
    timestamp: int
    clientInfo: str
    exchangeInfo: str
    quotes: list[SqfQuoteReply]


class SqfMlQuoteReplyMessage(App1SqfMessage, direction='outgoing', indicator=117):
    __test__ = False

    class BodyRecord(Record):
        Fields = [
            Field('quoteMessageId', LongBE),
            Field('timestamp', LongBE),
            Field('orderbookId', IntBE),
            Field('responseCode', IntBE),
            Field('clientInfo', FixedAsciiString(16)),
            Field('exchangeInfo', FixedAsciiString(32)),
            Field('quoteReplies', Array(MlQuoteReply, length_type=ShortBE)),
        ]

    quoteMessageId: int
    orderbookId: int
    timestamp: int
    responseCode: int
    clientInfo: str
    exchangeInfo: str
    quotes: list[MlQuoteReply]
