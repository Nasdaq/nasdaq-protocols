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


def test__fix_parser__parse__xml_with_service_pack(tmp_file_writer):
    fix_502 = '''
    <fix major="5" minor="0" servicepack="2">
    </fix>
    '''
    file = tmp_file_writer(fix_502)

    definitions = parse(file)
    assert definitions.version == 502


def test__fix_parser__parse__xml_with_keywords__keywords_are_transformed(tmp_file_writer):
    fix_502 = '''
    <fix major="5" minor="0" servicepack="2">
        <fields>
            <field number="35" name="MsgType" type="STRING" >
                <value enum="0" description="None" />
                <value enum="1" description="if" />
            </field>
        </fields>
    </fix>
    '''
    file = tmp_file_writer(fix_502)

    definitions = parse(file)
    assert definitions.version == 502
    context = definitions.fields['MsgType'].get_codegen_context(None)
    assert context['values'][0]['f_value'] == 'None_'
    assert context['values'][1]['f_value'] == 'if_'


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

    assert_component('InstrmtLegGrp', ('PossResend', False), ('QuoteStatus', False))
    assert_component('Instrument', ('PossResend', True), ('QuoteStatus', True))
    assert_component('InstrumentExtensionNoInstrAttribSubGroup', ('PossResend', True), ('QuoteStatus', False))
    assert 'GroupOfComponents' in fix_44_definitions.components
    assert_group(
        'NoLegs',
        fix_44_definitions.components['GroupOfComponents'].entries[0],
        ('PossResend', False), ('QuoteStatus', False)
    )
    assert_group(
        'NoStreams',
        fix_44_definitions.components['GroupOfComponents'].entries[1],
        ('PossResend', True), ('QuoteStatus', True)
    )


def test__fix_parser__header_is_parsed(fix_44_definitions):
    assert len(fix_44_definitions.header.entries) == 2
    assert fix_44_definitions.header.entries[0].field.name == 'BeginString'
    assert fix_44_definitions.header.entries[0].field.tag == '8'
    assert fix_44_definitions.header.entries[0].field.type == FixString
    assert fix_44_definitions.header.entries[0].required
    assert fix_44_definitions.header.entries[1].field.name == 'BodyLength'
    assert fix_44_definitions.header.entries[1].field.tag == '9'
    assert fix_44_definitions.header.entries[1].field.type == FixInt
    assert not fix_44_definitions.header.entries[1].required


def test__fix_parser__trailer_is_parsed(fix_44_definitions):
    assert len(fix_44_definitions.trailer.entries) == 1
    assert fix_44_definitions.trailer.entries[0].field.name == 'CheckSum'
    assert fix_44_definitions.trailer.entries[0].field.tag == '10'
    assert fix_44_definitions.trailer.entries[0].field.type == FixString
    assert fix_44_definitions.trailer.entries[0].required


def test__fix_parser__message_is_parsed(fix_44_definitions):
    assert len(fix_44_definitions.messages) == 1
    message = fix_44_definitions.messages[0]

    assert message.tag == 'A'
    assert message.name == 'Logon'
    assert message.category == 'Session'

    assert len(message.entries) == 4
    assert message.entries[0].field.name == 'HeartBtInt'
    assert message.entries[0].required
    assert message.entries[1].field.name == 'PossResend'
    assert not message.entries[1].required
    assert message.entries[2].field.name == 'QuoteStatus'
    assert not message.entries[2].required
    assert_group(
        'NoStreams',
        message.entries[3],
        ('PossResend', True), ('QuoteStatus', True)
    )


def assert_group(name, group, *fields_defn):
    assert name == group.name
    assert len(group.entries) == len(fields_defn)
    for i, field_defn in enumerate(fields_defn):
        field = group.entries[i]
        assert field.field.name == field_defn[0]
        assert field.required == field_defn[1]
