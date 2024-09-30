import importlib.util
from pathlib import Path
import os
import sys
import pytest

from click.testing import CliRunner
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


@pytest.fixture(scope='function')
def codegen_invoker(tmp_path):
    def generator(codegen, xml_content, app_name, generate_init_file, prefix):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open('spec.xml', 'w') as spec_file:
                spec_file.write(xml_content)
            Path('output').mkdir(parents=True, exist_ok=True)
            result = runner.invoke(
                codegen,
                [
                    '--spec-file', 'spec.xml',
                    '--app-name', app_name,
                    '--op-dir', 'output',
                    '--prefix', prefix,
                    '--init-file' if generate_init_file else '--no-init-file'
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


@pytest.fixture(scope='function')
def tools_codegen_invoker(tmp_path):
    def generator(codegen, app_name, package):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
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