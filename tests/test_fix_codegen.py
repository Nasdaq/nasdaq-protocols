import importlib
import os
import sys
from pathlib import Path

import pytest

from nasdaq_protocols.fix import codegen
from nasdaq_protocols.fix.parser import parse
from tests.testdata import TEST_FIX_44_XML, TEST_XML_ITCH_MESSAGE


@pytest.fixture(scope='function')
def fix_44_definitions(tmp_file_writer):
    file = tmp_file_writer(TEST_FIX_44_XML)
    definitions = parse(file)
    assert definitions is not None
    yield definitions


def test__no_init_file__no_prefix__code_generated(codegen_invoker):
    prefix = ''
    app_name = 'gwy_44'
    generated_files = codegen_invoker(
        codegen.generate,
        TEST_FIX_44_XML,
        app_name,
        generate_init_file=False,
        prefix=prefix
    )

    assert len(generated_files) == 5


def test__init_file__no_prefix__code_generated(fix_44_definitions, codegen_invoker, tmp_path, module_loader):
    prefix = ''
    app_name = 'gwy_44'
    output_dir = tmp_path / app_name
    generated_files = codegen_invoker(
        codegen.generate,
        TEST_FIX_44_XML,
        app_name,
        generate_init_file=True,
        prefix=prefix,
        output_dir=output_dir
    )

    assert len(generated_files) == 6

    # This ensures the generated code is correct
    generated_package = module_loader('test__init_file__no_prefix__code_generated', output_dir / '__init__.py')

    for field in fix_44_definitions.fields:
        assert hasattr(generated_package, field)

    for message in fix_44_definitions.messages:
        assert hasattr(generated_package, message.name)
