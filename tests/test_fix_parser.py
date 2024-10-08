import pytest

from nasdaq_protocols.fix import FixString, FixInt, FixBool
from nasdaq_protocols.fix.parser.parser import parse
from tests.testdata import TEST_FIX_44_XML


@pytest.fixture(scope='function')
def fix_44_definitions(tmp_file_writer):
    file = tmp_file_writer(TEST_FIX_44_XML)
    definitions = parse(file)
    assert definitions is not None
    yield definitions


def test__fix_parser__parse__invalid_root_tag(tmp_file_writer):
    invalid_xml = '''
    <fix_44>
    </fix_44>
    '''
    file = tmp_file_writer(invalid_xml)

    with pytest.raises(ValueError) as e:
        parse(file)

    assert str(e.value) == 'root tag is not fix'


def test__fix_parser__parse__invalid_tag_in_fields(tmp_file_writer):
    invalid_xml = '''
    <fix major="4" minor="4">
        <fields>
            <invalid/>
        </fields>
    </fix>
    '''
    file = tmp_file_writer(invalid_xml)

    with pytest.raises(ValueError) as e:
        parse(file)

    assert str(e.value) == 'expected field tag, got invalid'


def test__fix_parser__parse__unsupported_version(tmp_file_writer):
    invalid_xml = '''
    <fix major="2" minor="1">
        <fields>
            <invalid/>
        </fields>
    </fix>
    '''
    file = tmp_file_writer(invalid_xml)

    with pytest.raises(ValueError) as e:
        parse(file)

    assert str(e.value) == 'Version 21 is not supported'


def test__fix_parser__parse__component_not_found(tmp_file_writer):
    invalid_xml = '''
    <fix major="4" minor="4">
        <components>
            <component name="Testable">
                <group name="test" required="N">
                    <component name="NotFoundComponent" required="Y"/>
                </group>
            </component>
        </components>
    </fix>
    '''
    file = tmp_file_writer(invalid_xml)

    with pytest.raises(ValueError) as e:
        parse(file)

    assert str(e.value) == 'Component definition for NotFoundComponent not found'


def test__fix_parser__parse__field_not_found(tmp_file_writer):
    invalid_xml = '''
    <fix major="4" minor="4">
        <components>
            <component name="Testable">
                <field name="NotFound" required="N"/>
            </component>
        </components>
    </fix>
    '''
    file = tmp_file_writer(invalid_xml)

    with pytest.raises(ValueError) as e:
        parse(file)

    assert str(e.value) == 'Field definition for NotFound not found'


def test__fix_parser__fields_are_parsed(fix_44_definitions):
    def assert_field(name, tag, typ, total_possible_values):
        assert name in fix_44_definitions.fields
        assert fix_44_definitions.fields[name].tag == tag
        assert fix_44_definitions.fields[name].name == name
        assert fix_44_definitions.fields[name].type == typ
        assert len(fix_44_definitions.fields[name].possible_values) == total_possible_values

    assert_field('BeginString', '8', FixString, 0)
    assert_field('BodyLength', '9', FixInt, 0)
    assert_field('MsgType', '35', FixString, 2)
    assert_field('PossResend', '97', FixBool, 2)
    assert_field('QuoteStatus', '297', FixInt, 3)


def test__fix_parser__components_are_parsed(fix_44_definitions):
    def assert_component(name, *fields_defn):
        assert name in fix_44_definitions.components
        assert len(fix_44_definitions.components[name].entries) == len(fields_defn)
        for i, field_defn in enumerate(fields_defn):
            field = fix_44_definitions.components[name].entries[i]
            assert field.required == field_defn[1]
            assert field.field.name == field_defn[0]

    def assert_group(name, group, *fields_defn):
        assert name == group.name
        assert len(group.entries) == len(fields_defn)
        for i, field_defn in enumerate(fields_defn):
            field = group.entries[i]
            assert field.field.name == field_defn[0]
            assert field.required == field_defn[1]

    assert_component('InstrmtLegGrp', ('PossResend', False), ('QuoteStatus', False))
    assert_component('Instrument', ('PossResend', True), ('QuoteStatus', True))
    assert_component('InstrumentExtensionNoInstrAttribSubGroup', ('PossResend', True), ('QuoteStatus', False))
    assert 'GroupOfComponents' in fix_44_definitions.components
    assert_group(
        'InstrmtLegGrp_Group',
        fix_44_definitions.components['GroupOfComponents'].entries[0],
        ('PossResend', False), ('QuoteStatus', False)
    )
    assert_group(
        'Instrument_Group',
        fix_44_definitions.components['GroupOfComponents'].entries[1],
        ('PossResend', True), ('QuoteStatus', True)
    )