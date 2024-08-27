from nasdaq_protocols import soup
from nasdaq_protocols.soup._reader import SoupMessageReader

from .reader_app_tests import *


INPUT1 = soup.LoginRequest('nouser', 'nopassword', 'session', '1')
INPUT2 = soup.LoginAccepted('session', 10)
MESSAGES = {
    0: soup.LogoutRequest(),
    1: INPUT1,
    2: INPUT2
}


def input_factory(id_):
    len_, bytes_ = MESSAGES[id_].to_bytes()
    return bytes_


def output_factory(id_):
    return MESSAGES[id_]


async def test__fix_reader__all_basic_tests_pass(reader_clientapp_common_tests):
    await reader_clientapp_common_tests(
        SoupMessageReader,
        input_factory,
        output_factory
    )
