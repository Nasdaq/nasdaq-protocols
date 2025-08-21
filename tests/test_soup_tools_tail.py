import asyncio
import concurrent.futures
import logging

import pytest
from click.testing import CliRunner

from nasdaq_protocols import soup
from nasdaq_protocols.soup.tools_soup_tail import command as soup_tail_command

from tests.mocks import matches, send


LOG = logging.getLogger(__name__)
pytestmark = pytest.mark.xfail(reason="Known Linux system error")


@pytest.mark.parametrize('request_sequence, response_sequence, messages_to_send', [
    (1, 1, 100),   # connect from begin, send 100 messages
    (0, 100, 1),   # connect to head, server will send the 100th message
    (50, 50, 50),  # connect to a specific message, server will send 50 messages starting from 50
    (100, 101, 0)  # connect to a specific message, server will send no messages, but close the connection
])
async def test__soup__tools__soup_tail__connect_from_begin(mock_server_session,
                                                           request_sequence, response_sequence, messages_to_send):
    port, server_session = mock_server_session
    server_session_closed = asyncio.Event()
    event_loop = asyncio.get_running_loop()

    server_session = configure_streaming_messages(server_session, request_sequence, response_sequence, messages_to_send)

    # close the server session after 3 seconds
    event_loop.call_later(3, close_server_session, server_session, server_session_closed)

    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await event_loop.run_in_executor(pool, invoke_soup_tail_cmd, '127.0.0.1', port, request_sequence)
        await server_session_closed.wait()

    assert result['exit_code'] == 0, f"Command failed with exit code {result['exit_code']}"
    assert_soup_tail_output(result, response_sequence, messages_to_send)


async def test__soup__tools__soup_tail__login_rejected(mock_server_session):
    port, server_session = mock_server_session
    event_loop = asyncio.get_running_loop()

    # Configure the server to reject login
    server_session.when(
        matches(soup.LoginRequest('test-u', 'test-p', 'session', '1')),
        'login-request-match',
    ).do(
        send(soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)),
        'send-login-rejected'
    )

    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await event_loop.run_in_executor(pool, invoke_soup_tail_cmd, '127.0.0.1', port, 1)

    assert result['exit_code'] == 1, f"Command should have failed with exit code {result['exit_code']}"


async def test__soup__tools__soup_tail__unable_to_connect(unused_tcp_port):
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await asyncio.get_running_loop().run_in_executor(
            pool, invoke_soup_tail_cmd, '127.0.1', unused_tcp_port, 1
        )
    assert result['exit_code'] == 1, f"Command should have failed with exit code {result['exit_code']}"


def assert_soup_tail_output(result, response_sequence, messages_to_send):
    # Prepare expected output
    expected_output = [
        f"{i + response_sequence} : b'server-sends-{response_sequence + i}'" for i in range(messages_to_send)
    ]
    expected_output.append('debug message from server')
    expected_output.append('connection closed.')

    actual_output = [line for line in result['stdout'].decode('ascii').split('\n') if line != '']
    assert actual_output == expected_output, f"Expected: {expected_output}, but got: {actual_output}"


def configure_streaming_messages(server_session, request_sequence, response_sequence, messages_to_send=10):
    """
    Configures the mock server session to respond to a login request and send a sequence of messages.
    """
    server_session.when(
        matches(soup.LoginRequest('test-u', 'test-p', 'session', str(request_sequence))),
        'login-request-match',
    ).do(
        send(soup.LoginAccepted('session', response_sequence or request_sequence)),
        'send-login-accepted'
    ).do(
        lambda session, _data: [session.send(soup.SequencedData(f'server-sends-{response_sequence + i}'.encode())) for i in range(messages_to_send)],
        'send-sequenced-data-stream',
    ).do(
        lambda session, _data: session.send(soup.Debug('debug message from server')),
        'send-debug-message',
    )
    return server_session


def invoke_cli_cmd(cmd, *args, **kwargs):
    runner = CliRunner()
    result = runner.invoke(cmd, args, **kwargs)
    return {
        'stdout': result.stdout_bytes,
        'stderr': result.stderr_bytes,
        'return_value': result.return_value,
        'exit_code': result.exit_code,
    }


def invoke_soup_tail_cmd(ip, port, sequence):
    return invoke_cli_cmd(
        soup_tail_command,
        '-h', ip,
        '-p', str(port),
        '-U', 'test-u',
        '-P', 'test-p',
        '-S', 'session',
        '-s', str(sequence),
    )


def close_server_session(session, event):
    LOG.info('Closing server session')
    session.close()
    event.set()




