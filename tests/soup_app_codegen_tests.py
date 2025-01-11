import attrs
import pytest


SOUP_CODEGEN_TESTS = []


@attrs.define
class TestParams:
    codegen_invoker: callable
    code_loader: callable
    generator: callable
    app_name: str
    input_xml_str: str
    protocol: str
    expected_generated_code: str
    load_generated_code: any


def soup_codegen_test(target):
    SOUP_CODEGEN_TESTS.append(target)
    return target


@soup_codegen_test
def no_init_file__no_prefix__code_generated(params: TestParams):
    expected_file_name = f'{params.protocol}_{params.app_name}.py'
    generated_files = params.codegen_invoker(
        params.generator,
        params.input_xml_str,
        params.app_name,
        generate_init_file=False,
        prefix=''
    )

    assert len(generated_files) == 1
    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == params.expected_generated_code.strip()


@soup_codegen_test
def init_file__no_prefix__code_generated(params: TestParams):
    expected_file_name = f'{params.protocol}_{params.app_name}.py'
    generated_files = params.codegen_invoker(
        params.generator,
        params.input_xml_str,
        params.app_name,
        generate_init_file=True,
        prefix=''
    )

    assert len(generated_files) == 2

    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == params.expected_generated_code.strip()

    assert '__init__.py' in generated_files
    assert generated_files['__init__.py'].strip() == f'from .{params.protocol}_{params.app_name} import *'


@soup_codegen_test
def init_file__with_prefix__code_generated(params: TestParams):
    prefix = 'test'
    expected_file_name = f'{prefix}_{params.protocol}_{params.app_name}.py'
    generated_files = params.codegen_invoker(
        params.generator,
        params.input_xml_str,
        params.app_name,
        generate_init_file=True,
        prefix=prefix
    )

    assert len(generated_files) == 2

    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == params.expected_generated_code.strip()

    assert '__init__.py' in generated_files
    assert generated_files['__init__.py'].strip() == f'from .{prefix}_{params.protocol}_{params.app_name} import *'


@soup_codegen_test
def load_generated_code__code_loads_without_issue(params: TestParams):
    assert params.load_generated_code is not None


@pytest.fixture(scope='function', params=SOUP_CODEGEN_TESTS)
async def soup_clientapp_codegen_tests(request, codegen_invoker, code_loader):
    async def define_test(protocol,
                          app_name,
                          generator,
                          input_xml_str,
                          expected_code,
                          load_generated_code):
        # every test is executed here.
        request.param(
            TestParams(
                codegen_invoker=codegen_invoker,
                code_loader=code_loader,
                generator=generator,
                app_name=app_name,
                input_xml_str=input_xml_str,
                protocol=protocol,
                expected_generated_code=expected_code,
                load_generated_code=load_generated_code
            )
        )

    yield define_test
