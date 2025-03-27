import asyncio
import importlib.util
import logging
import threading
from pathlib import Path
import os
import sys
import pytest

from click.testing import CliRunner
from nasdaq_protocols import common
from .mocks import *


LOG = logging.getLogger(__name__)


@pytest.fixture(scope='function', autouse=True)
def thread_resource_clean_checker():
    before_threads = [thread.name for thread in threading.enumerate()]
    yield
    after_threads = [thread.name for thread in threading.enumerate()]

    if before_threads != after_threads:
        LOG.warning(f'Threads differ: {before_threads=} {after_threads=}')
        new_threads = [thread for thread in after_threads if thread not in before_threads]
        LOG.warning(f'New threads: {new_threads}')


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


@pytest.fixture(scope='function')
def sync_mock_server_session(unused_tcp_port):
    event_loop = asyncio.new_event_loop()
    thread = threading.Thread(name=f'mock-server', target=event_loop.run_forever)
    thread.start()

    session = MockServerSession()
    future = asyncio.run_coroutine_threadsafe(
        common.start_server(('127.0.0.1', unused_tcp_port), lambda: session),
        event_loop
    )
    server, serving_task = future.result()
    LOG.debug('Mock Server started')

    yield unused_tcp_port, session
    future = asyncio.run_coroutine_threadsafe(common.stop_task(serving_task), event_loop)
    future.result()
    event_loop.call_soon_threadsafe(event_loop.stop)
    thread.join()


@pytest.fixture(scope='function')
def codegen_invoker(capsys, tmp_path):
    def generator(codegen, xml_content, app_name, generate_init_file, prefix, output_dir=None, extra_args=None):
        runner = CliRunner()
        with capsys.disabled(), runner.isolated_filesystem(temp_dir=tmp_path):
            with open('spec.xml', 'w') as spec_file:
                spec_file.write(xml_content)
            output_dir = output_dir or 'output'
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            extra_args = extra_args or []
            result = runner.invoke(
                codegen,
                [
                    '--spec-file', 'spec.xml',
                    '--app-name', app_name,
                    '--op-dir', output_dir,
                    '--prefix', prefix,
                    '--init-file' if generate_init_file else '--no-init-file',
                    *extra_args
                ]
            )
            assert result.exit_code == 0

            # Read the generated files
            generated_file_contents = {}
            for file in os.listdir(output_dir):
                with open(os.path.join(output_dir, file)) as f:
                    generated_file_contents[file] = f.read()
            return generated_file_contents
    return generator


@pytest.fixture(scope='function')
def tools_codegen_invoker(capsys, tmp_path):
    def generator(codegen, app_name, package):
        runner = CliRunner()
        with capsys.disabled(), runner.isolated_filesystem(temp_dir=tmp_path):
            Path('output').mkdir(parents=True, exist_ok=True)
            result = runner.invoke(
                codegen,
                [
                    '--op-dir', 'output',
                    '--app-name', app_name,
                    '--package', package
                ]
            )
            assert result.exit_code == 0

            # Read the generated files
            generated_file_contents = {}
            for file in os.listdir('output'):
                with open(os.path.join('output', file)) as f:
                    generated_file_contents[file] = f.read()
            return generated_file_contents
    return generator


@pytest.fixture(scope='session')
def code_loader():
    def loader_(module_name, code_as_string):
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module_ = importlib.util.module_from_spec(spec)
        exec(code_as_string, module_.__dict__)
        sys.modules[module_name] = module_
        return module_
    return loader_


@pytest.fixture(scope='session')
def module_loader():
    def load_module(module_name, file):
        spec = importlib.util.spec_from_file_location(module_name, file)
        assert spec is not None
        generated_package = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = generated_package
        spec.loader.exec_module(generated_package)
        return generated_package
    return load_module


@pytest.fixture(scope='function')
def package_loader():
    loaded_packages_path = []

    def load_package(package_name, package_dir):
        sys.path.insert(0, str(package_dir))
        package_ = importlib.import_module(package_name)
        loaded_packages_path.append(str(package_dir))
        return package_

    yield load_package

    for pkg_path in loaded_packages_path:
        sys.path.remove(pkg_path)
