import os
import pytest

from nasdaq_protocols import common
from .mocks import *


@pytest.fixture(scope='function')
def tmp_file_writer(tmp_path):
    """
    Fixture that returns a file writer.

    The returned filewriter can be called with a string to write to a temporary file.
    The filename is returned and the file is deleted after the test.
    """
    tmp_xml_file = os.path.join(tmp_path, 'test.xml')

    def write_file(data):

        with open(tmp_xml_file, 'w') as file:
            file.write(data)
        return tmp_xml_file

    yield write_file

    os.remove(tmp_xml_file)


@pytest.fixture(scope='function')
async def mock_server_session(unused_tcp_port):
    session = MockServerSession()
    server, serving_task = await common.start_server(('127.0.0.1', unused_tcp_port), lambda: session)
    yield unused_tcp_port, session
    await common.stop_task(serving_task)