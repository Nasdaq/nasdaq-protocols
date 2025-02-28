import importlib.resources
import logging
from pathlib import Path

import pytest
import sys


@pytest.fixture(scope='function')
def asn1_spec_creator(tmpdir):
    def create(spec_content, spec_dir_name='test_spec'):
        Path(tmpdir / spec_dir_name).mkdir(parents=True, exist_ok=True)
        with open(tmpdir / spec_dir_name / f'test.asn1', 'w') as spec_file:
            spec_file.write(spec_content)
        with open(tmpdir / spec_dir_name / '__init__.py', 'w') as spec_file:
            ...
    return create


def test__asn1_spec__compile(asn1_spec_creator):
    spec = """
    MyShopPurchaseOrders DEFINITIONS AUTOMATIC TAGS ::= BEGIN

    OrderType ::= ENUMERATED
    {
        retail(0),
        wholesale(1)
    }
    """
    spec_dir = asn1_spec_creator(spec)
    
