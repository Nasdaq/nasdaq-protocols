import logging
import os

import pytest
from click.testing import CliRunner
from nasdaq_protocols.asn1_app import generate_soup_app
from tests.testdata import TEST_ASN1_SPEC


LOG = logging.getLogger(__name__)
EXPECTED_GENERATED_CODE = """
from typing import Callable, Awaitable, Type

from nasdaq_protocols.common import logable, asn1
from nasdaq_protocols import asn1_app

__all__ = [
    'OrderType',
    'Address',
    'CustomerInfo',
    'Item',
    'ListOfItems',
    'PurchaseOrder',
    'PurchaseQuote',
    'MyCompanyAutomation',
    'Message',
    'SoupClientSession',
    'connect_async_soup'
]


class OrderType(asn1.Asn1Enum):
    retail = 0
    wholesale = 1


class Address(asn1.Asn1Sequence):
    Fields = {
        'street': str,
        'city': str,
        'state': str,
        'zipCode': str,
    }

    def has_street(self) -> bool:
        return 'street' in self

    def has_city(self) -> bool:
        return 'city' in self

    def has_state(self) -> bool:
        return 'state' in self

    def has_zipCode(self) -> bool:
        return 'zipCode' in self

    street: str
    city: str
    state: str
    zipCode: str


class CustomerInfo(asn1.Asn1Sequence):
    Fields = {
        'companyName': str,
        'billingAddress': Address,
        'contactPhone': str,
    }

    def has_companyName(self) -> bool:
        return 'companyName' in self

    def has_billingAddress(self) -> bool:
        return 'billingAddress' in self

    def has_contactPhone(self) -> bool:
        return 'contactPhone' in self

    companyName: str
    billingAddress: Address
    contactPhone: str


class Item(asn1.Asn1Sequence):
    Fields = {
        'itemCode': int,
        'color': str,
        'power': int,
    }

    def has_itemCode(self) -> bool:
        return 'itemCode' in self

    def has_color(self) -> bool:
        return 'color' in self

    def has_power(self) -> bool:
        return 'power' in self

    itemCode: int
    color: str
    power: int


class ListOfItems(asn1.Asn1SequenceOf):
    Fields = {
        'Item': Item,
    }

    def has_Item(self) -> bool:
        return 'Item' in self

    Item: list[Item]


class PurchaseOrder(asn1.Asn1Sequence):
    Fields = {
        'dateOfOrder': str,
        'customer': CustomerInfo,
        'orderType': OrderType,
        'items': ListOfItems,
    }

    def has_dateOfOrder(self) -> bool:
        return 'dateOfOrder' in self

    def has_customer(self) -> bool:
        return 'customer' in self

    def has_orderType(self) -> bool:
        return 'orderType' in self

    def has_items(self) -> bool:
        return 'items' in self

    dateOfOrder: str
    customer: CustomerInfo
    orderType: OrderType
    items: ListOfItems


class PurchaseQuote(asn1.Asn1Sequence):
    Fields = {
        'quoteId': int,
        'itemName': str,
        'itemPrice': int,
        'itemQty': int,
        'extension': bytes,
    }

    def has_quoteId(self) -> bool:
        return 'quoteId' in self

    def has_itemName(self) -> bool:
        return 'itemName' in self

    def has_itemPrice(self) -> bool:
        return 'itemPrice' in self

    def has_itemQty(self) -> bool:
        return 'itemQty' in self

    def has_extension(self) -> bool:
        return 'extension' in self

    quoteId: int
    itemName: str
    itemPrice: int
    itemQty: int
    extension: bytes


class MyCompanyAutomation(asn1.Asn1Choice):
    Fields = {
        'purchaseOrder': PurchaseOrder,
        'purchaseQuote': PurchaseQuote,
    }

    def has_purchaseOrder(self) -> bool:
        return 'purchaseOrder' in self

    def has_purchaseQuote(self) -> bool:
        return 'purchaseQuote' in self

    purchaseOrder: PurchaseOrder
    purchaseQuote: PurchaseQuote


# spec
class Myasn1app(asn1.Asn1Spec, spec_name='MyAsn1App', spec_pkg_dir='.spec'):
    ...


@logable
class Message(asn1.Asn1Message, spec=Myasn1app, pdu_name='MyShopPurchaseOrders'):
    ...


class SoupClientSession(asn1_app.Asn1SoupClientSession, asn1_message=Message):
    ...


async def connect_async_soup(remote: tuple[str, int], user: str, passwd: str, session_id,
                             sequence: int = 0,
                             on_msg_coro: Callable[[Type[asn1.Asn1Message]], Awaitable[None]] = None,
                             on_close_coro: Callable[[], Awaitable[None]] = None,
                             client_heartbeat_interval: int = 10,
                             server_heartbeat_interval: int = 10) -> SoupClientSession:
    def session_factory(x):
        return SoupClientSession(x, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)

    return await asn1_app.connect_async_soup(
        remote, user, passwd, session_id, session_factory,
        sequence,
        client_heartbeat_interval, server_heartbeat_interval
    )


"""


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


@pytest.fixture(scope='function')
def asn1_codegen_invoker(capsys, tmp_path):
    def generator(codegen, asn1_content, pdu, app_name, generate_init_file, prefix, extra_args=None, expected_exit_code=0):
        runner = CliRunner()
        with capsys.disabled(), runner.isolated_filesystem(temp_dir=tmp_path):
            in_spec_dir = tmp_path / 'in_spec'
            output_dir = tmp_path / 'output'
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
                    '--package-name', '',
                    '--init-file' if generate_init_file else '--no-init-file',
                    *extra_args
                ]
            )
            assert result.exit_code == expected_exit_code

            # Read the generated files
            return read_dir(output_dir)
    return generator


@pytest.mark.parametrize('prefix', ['', 'Prefix'])
def test__asn1_codegen__no_init_file__no_prefix__code_generated(asn1_codegen_invoker, prefix):
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
    with open(f'{file_prefix}{generated_py_module}', 'w') as file:
        file.write(EXPECTED_GENERATED_CODE)


@pytest.mark.parametrize('prefix', ['', 'Prefix'])
def test__asn1_codegen__init_file__no_prefix__code_generated(asn1_codegen_invoker, prefix):
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


def test__asn1_codegen__not_implemented_type__raises_error(asn1_codegen_invoker):
    spec = """
    MyShopPurchaseOrders DEFINITIONS AUTOMATIC TAGS ::= BEGIN

    MyCompanyAutomation ::= SET {
        id INTEGER,
        name UTF8String
    }
    END
    """
    asn1_codegen_invoker(
        generate_soup_app,
        asn1_content=spec,
        pdu='MyShopPurchaseOrders',
        app_name='MyAsn1App',
        generate_init_file=False,
        prefix='',
        expected_exit_code=1
    )