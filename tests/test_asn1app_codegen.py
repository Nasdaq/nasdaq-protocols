import importlib
import logging
import os

import attrs
import asn1tools
import pytest
from click.testing import CliRunner
from nasdaq_protocols.asn1_app import generate_soup_app
from nasdaq_protocols.common import Serializable
from .soup_client_app_tests import soup_clientapp_common_tests
from tests.testdata import TEST_ASN1_SPEC


LOG = logging.getLogger(__name__)
EXPECTED_GENERATED_CODE = """
from typing import Callable, Awaitable, Type

from nasdaq_protocols.common import logable
from nasdaq_protocols import asn1_app

__all__ = [
    'Myasn1app',
    'Message',
    'SoupClientSession',
    'connect_async_soup'
]


# spec
class Myasn1app(asn1_app.Asn1Spec, spec_name='MyAsn1App', spec_pkg_dir='test.spec'):
    ...


@logable
class Message(asn1_app.Asn1Message, spec=Myasn1app, pdu_name='MyShopPurchaseOrders'):
    ...


class SoupClientSession(asn1_app.Asn1SoupClientSession, asn1_message=Message):
    ...


async def connect_async_soup(remote: tuple[str, int], user: str, passwd: str, session_id,
                             sequence: int = 0,
                             session_factory: Callable[[], SoupClientSession]= None,
                             on_msg_coro: Callable[[Type[asn1_app.Asn1Message]], Awaitable[None]] = None,
                             on_close_coro: Callable[[], Awaitable[None]] = None,
                             client_heartbeat_interval: int = 10,
                             server_heartbeat_interval: int = 10) -> SoupClientSession:
    def session_factory_default(x):
        return SoupClientSession(x, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)

    session_factory = session_factory or session_factory_default

    return await asn1_app.connect_async_soup(
        remote, user, passwd, session_id, session_factory,
        sequence,
        client_heartbeat_interval, server_heartbeat_interval
    )


"""
compiler = asn1tools.compile_string(TEST_ASN1_SPEC)


@attrs.define(auto_attribs=True)
class TestHurlMessage(Serializable):
    data: bytes

    def to_bytes(self) -> tuple[int, bytes]:
        return len(self.data), self.data

    def from_bytes(cls, bytes_: bytes):
        raise NotImplementedError


def read_dir(dir_path):
    generated_file_contents: dict[str, str|dict] = {}
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            generated_file_contents[file] = read_dir(file_path)
        else:
            with open(file_path) as f:
                generated_file_contents[file] = f.read()
    return generated_file_contents


def get_test_msg(i):
    purchase_order = {
        'dateOfOrder': str(i),
        'customer': {
            'companyName': 'MyCompany',
            'billingAddress': {
                'street': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zipCode': '12345'
            },
            'contactPhone': '1234567890'
        },
        'orderType': 'retail',
        'items': [
            {
                'itemCode': 1,
                'color': 'Black',
                'power': 110
            }
        ]
    }

    my_company_automation = ('purchaseOrder', purchase_order)
    return my_company_automation


@pytest.fixture(scope='function')
def asn1_codegen_invoker(capsys, tmp_path):
    def generator(codegen, asn1_content, pdu, app_name, generate_init_file, prefix,
                  extra_args=None, expected_exit_code=0,
                  output_module_name='output',
                  package_name='test'):
        runner = CliRunner()
        with capsys.disabled(), runner.isolated_filesystem(temp_dir=tmp_path):
            in_spec_dir = tmp_path / 'in_spec'
            output_dir = tmp_path / package_name
            in_spec_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(f'{in_spec_dir}/test_{app_name}.asn1', 'w') as asn1_file:
                asn1_file.write(asn1_content)

            extra_args = extra_args or []
            result = runner.invoke(
                codegen,
                [
                    '--asn1-files-dir', in_spec_dir,
                    '--app-name', app_name,
                    '--pdu-name', pdu,
                    '--prefix', prefix,
                    '--op-dir', output_dir,
                    '--package-name', package_name,
                    '--init-file' if generate_init_file else '--no-init-file',
                    *extra_args
                ]
            )
            assert result.exit_code == expected_exit_code

            # Read the generated files
            op = read_dir(output_dir)
            op['output_dir'] = tmp_path
            op['output_module_path'] = output_dir
            return op
    return generator


@pytest.mark.parametrize('prefix', ['', 'Prefix1'])
def test__asn1app_codegen__no_init_file__no_prefix__code_generated(asn1_codegen_invoker, prefix):
    file_prefix = f'{prefix}_' if prefix else ''
    app_name = 'MyAsn1App'
    generated_py_module = f'{file_prefix}{app_name}.py'
    generated_asn1 = f'test_{app_name}.asn1'
    generated_files = asn1_codegen_invoker(
        generate_soup_app,
        asn1_content=TEST_ASN1_SPEC,
        pdu='MyShopPurchaseOrders',
        app_name=app_name,
        generate_init_file=False,
        prefix=prefix
    )
    assert generated_py_module in generated_files
    assert generated_files[generated_py_module].strip() == EXPECTED_GENERATED_CODE.strip()

    assert 'spec' in generated_files
    assert generated_asn1 in generated_files['spec']
    assert generated_files['spec'][generated_asn1].strip() == TEST_ASN1_SPEC.strip()

    assert '__init__.py' not in generated_files


@pytest.mark.parametrize('prefix', ['', 'Prefix2'])
def test__asn1app_codegen__init_file__no_prefix__code_generated(asn1_codegen_invoker, prefix):
    file_prefix = f'{prefix}_' if prefix else ''
    app_name = 'MyAsn1App'
    generated_py_module = f'{file_prefix}{app_name}.py'
    generated_asn1 = f'test_{app_name}.asn1'
    generated_files = asn1_codegen_invoker(
        generate_soup_app,
        asn1_content=TEST_ASN1_SPEC,
        pdu='MyShopPurchaseOrders',
        app_name=app_name,
        generate_init_file=True,
        prefix=prefix
    )
    assert generated_py_module in generated_files
    assert generated_files[generated_py_module].strip() == EXPECTED_GENERATED_CODE.strip()

    assert 'spec' in generated_files
    assert generated_asn1 in generated_files['spec']
    assert generated_files['spec'][generated_asn1].strip() == TEST_ASN1_SPEC.strip()

    assert '__init__.py' in generated_files
    assert f'from .{file_prefix}MyAsn1App import *' in generated_files['__init__.py'].strip()


def test__asn1app_codegen__invalid_message__return_empty_message(asn1_codegen_invoker, package_loader):
    generated_files = asn1_codegen_invoker(
        generate_soup_app,
        asn1_content=TEST_ASN1_SPEC,
        pdu='MyCompanyAutomation',
        app_name='MyAsn1App',
        generate_init_file=True,
        prefix='',
        package_name='test'
    )

    package_ = package_loader('test', generated_files['output_dir'])
    assert package_.Message.from_bytes(b'') == (0, {})


def test__asn1app_codegen__invalid_asn1_spec__raises_error_when_using(asn1_codegen_invoker, package_loader):
    generated_files = asn1_codegen_invoker(
        generate_soup_app,
        asn1_content='Invalid ASN1 Spec',
        pdu='MyShopPurchaseOrders',
        app_name='InvalidApp',
        generate_init_file=True,
        prefix='',
        package_name='test_1'
    )
    with pytest.raises(Exception) as error:
        package_loader('test_1', generated_files['output_dir'])


async def test__asn1app_codegen__soup_clientapp_common_tests__using_generated_code(
        asn1_codegen_invoker, package_loader, soup_clientapp_common_tests):
    generated_files = asn1_codegen_invoker(
        generate_soup_app,
        asn1_content=TEST_ASN1_SPEC,
        pdu='MyCompanyAutomation',
        app_name='MyAsn1App',
        generate_init_file=True,
        prefix='',
        package_name='test'
    )
    package_ = package_loader('test', generated_files['output_dir'])

    def in_msg_factory(i):
        msg = get_test_msg(i)
        encoded_message = compiler.encode('MyCompanyAutomation', msg)
        return TestHurlMessage(encoded_message)

    def out_msg_factory(i):
        msg = get_test_msg(i)
        return msg

    await soup_clientapp_common_tests(
        package_.connect_async_soup,
        package_.SoupClientSession,
        in_msg_factory,
        out_msg_factory
    )



