from nasdaq_protocols.fix import FixMessageReader
from .reader_app_tests import *
from .fix_messages import *


body0 = DataSegment_1.from_value({
    1: 2,
    2: 'body0'
})
body1 = DataSegment_1.from_value({
    1: 2,
    2: 'body1',
    22: [
        {
            1: 21,
            2: 'body1_inner'
        }
    ]
})
body2 = DataSegment_1.from_value({
    1: 2,
    2: 'body2',
    22: [
        {
            1: 21,
            2: 'body2_inner'
        }
    ]
})
message0 = Message_5({
    fix.MessageSegments.HEADER: DataSegment_Header.from_value({
        8: 'FIXT.1.1',
        9: body0.to_bytes()[0] + len(b'35=5') + 2,
        35: '5'
    }),
    fix.MessageSegments.BODY: body0,
    fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value({
        10: '100'
    })
})
message1 = Message_1({
    fix.MessageSegments.HEADER: DataSegment_Header.from_value({
        8: 'FIXT.1.1',
        9: body1.to_bytes()[0] + len(b'35=M') + 2,
        35: 'M'
    }),
    fix.MessageSegments.BODY: body1,
    fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value({
        10: '100'
    })
})
message2 = Message_1({
    fix.MessageSegments.HEADER: DataSegment_Header.from_value({
        8: 'FIXT.1.1',
        9: body2.to_bytes()[0] + len(b'35=M') + 2,
        35: 'M'
    }),
    fix.MessageSegments.BODY: body2,
    fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value({
        10: '100'
    })
})
messages = {
    0: message0,
    1: message1,
    2: message2
}


def input_factory(id_):
    len_, bytes_ = messages[id_].to_bytes()
    return bytes_


def output_factory(id_):
    return messages[id_]


async def test__fix_reader__all_basic_tests_pass(reader_clientapp_common_tests):
    await reader_clientapp_common_tests(
        FixMessageReader,
        input_factory,
        output_factory
    )
