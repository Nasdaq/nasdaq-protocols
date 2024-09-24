import pytest

from nasdaq_protocols.common.message import parser
from .testdata import *


def test__parser__empty_enum_fielddef__parse(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_EMPTY_ENUMS_ROOT))
    assert len(definitions.enums) == 0
    assert len(parser.FieldDef.Definitions) == 0


def test__parser__empty_enum_fields__codegen_context(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_EMPTY_ENUMS_ROOT))
    assert definitions.get_codegen_context() == {
        'enums': [],
        'messages': [],
        'records': [],
    }


def test__parser__enums__parse(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_ENUMS))

    assert 'test_enum' in definitions.enums
    assert isinstance(definitions.enums['test_enum'], parser.EnumDef)

    test_enum: parser.EnumDef = definitions.enums['test_enum']
    assert test_enum.name == 'test_enum'
    assert test_enum.type == 'uint_8'
    assert len(test_enum.values) == 2

    for idx, enum_val in enumerate(test_enum.values):
        assert isinstance(enum_val, parser.EnumVal)
        assert enum_val.name == f'enum_{idx+1}'
        assert enum_val.description == f'enum_{idx+1}_desc'
        assert enum_val.value == f'{idx+1}'


def test__parser__enums__codegen_context(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_ENUMS))
    assert definitions.get_codegen_context() == {
        'enums': [
            {
                'name': 'test_enum',
                'quote': False,
                'values': [
                    {'name': 'enum_1', 'value': '1'},
                    {'name': 'enum_2', 'value': '2'}
                ]
            }
        ],
        'messages': [],
        'records': [],
    }


def test__parser__records__parse(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_RECORDS))
    expected_fields = ['int_field1', 'array_field', 'override_name_for_field1_def', 'int_field2_def', 'enum_field']

    assert len(definitions.records) == 1
    assert 'test_record' in definitions.records

    record: parser.RecordDef = definitions.records['test_record']
    assert len(record.fields) == 5
    all_field_name = [record.name for record in record.fields]
    assert all(field_name in all_field_name for field_name in expected_fields)

    assert record.fields[0].name == 'int_field1'
    assert record.fields[0].type == 'uint_8'
    assert record.fields[0].default == '0'

    assert record.fields[1].name == 'array_field'
    assert record.fields[1].type == 'uint_2'
    assert record.fields[1].default is None
    assert record.fields[1].array == 'single'
    assert record.fields[1].length == '5'

    assert record.fields[2].name == 'override_name_for_field1_def'
    assert record.fields[2].type == 'uint_4'
    assert record.fields[2].default is None

    assert record.fields[3].name == 'int_field2_def'
    assert record.fields[3].type == 'uint_4'
    assert record.fields[3].default is None

    assert record.fields[4].name == 'enum_field'
    assert record.fields[4].type == 'enum:test_enum'
    assert record.fields[4].default is None


def test__parser__records__codegen_context(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_RECORDS))
    assert definitions.get_codegen_context() == {
        'enums': [
            {
                'name': 'test_enum',
                'quote': True,
                'values': [
                    {'name': 'enum_1', 'value': '1'},
                ]
            }
        ],
        'messages': [],
        'records': [
            {
                'name': 'test_record',
                'fields': [
                    {'name': 'int_field1', 'type': 'UnsignedLong', 'default': True, 'default_value': '0', 'hint': 'int', 'quote': False},
                    {'name': 'array_field', 'type': 'Array(UnsignedShort, UnsignedShort)', 'default': False, 'default_value': None, 'hint': 'list[int]', 'quote': False},
                    {'name': 'override_name_for_field1_def', 'type': 'UnsignedInt', 'hint': 'int', 'quote': False, 'default': False, 'default_value': None},
                    {'name': 'int_field2_def', 'type': 'UnsignedInt', 'hint': 'int', 'quote': False, 'default': False, 'default_value': None},
                    {'name': 'enum_field', 'type': 'CharAscii', 'hint': 'test_enum', 'quote': True, 'default': False, 'default_value': None}
                ]
            }
        ],
    }


def test__parser__messages__parse(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_MESSAGES))

    assert len(definitions.messages) == 1
    assert 'test_message' in [msg.name for msg in definitions.messages]

    message: parser.MessageDef = definitions.messages[0]
    assert message.name == 'test_message'
    assert message.id == '1'
    assert message.group == 'test_group'
    assert message.direction == 'incoming'
    assert len(message.fields) == 2

    assert message.fields[0].name == 'direct_int_field1'
    assert message.fields[0].type == 'uint_4'
    assert message.fields[0].ref is None

    assert message.fields[1].name == 'record_field'
    assert message.fields[1].type == 'record:test_record'
    assert message.fields[1].default is None


def test__parser__messages__codegen_context(tmp_file_writer):
    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_MESSAGES))

    assert definitions.get_codegen_context() == {
        'enums': [
            {
                'name': 'test_enum',
                'quote': True,
                'values': [
                    {'name': 'enum_1', 'value': '1'},
                ]
            }
        ],
        'messages': [
            {
                'name': 'test_message',
                'indicator': '1',
                'group': 'test_group',
                'direction': 'incoming',
                'fields': [
                    {'name': 'direct_int_field1', 'type': 'UnsignedInt', 'hint': 'int', 'quote': False, 'default': False, 'default_value': None},
                    {'name': 'record_field', 'type': 'test_record', 'hint': 'test_record', 'quote': False, 'default': False, 'default_value': None}
                ]
            }
        ],
        'records': [
            {
                'name': 'test_record',
                'fields': [
                    {'name': 'int_field1', 'type': 'UnsignedLong', 'default': True, 'default_value': '0', 'hint': 'int', 'quote': False},
                    {'name': 'array_field', 'type': 'Array(UnsignedShort, UnsignedShort)', 'default': False, 'default_value': None, 'hint': 'list[int]', 'quote': False},
                    {'name': 'override_name_for_field1_def', 'type': 'UnsignedInt', 'hint': 'int', 'quote': False, 'default': False, 'default_value': None},
                    {'name': 'int_field2_def', 'type': 'UnsignedInt', 'hint': 'int', 'quote': False, 'default': False, 'default_value': None},
                    {'name': 'enum_field', 'type': 'CharAscii', 'hint': 'test_enum', 'quote': True, 'default': False, 'default_value': None}
                ]
            }
        ],
    }


def test__parser__repeats_messages__no_overriding__parse(tmp_file_writer):
    with pytest.raises(ValueError):
        definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_MESSAGES_REPEAT), override_messages=False)


def test__parser__repeats_messages__overriding__parse(tmp_file_writer):

    definitions = parser.Parser.parse(tmp_file_writer(TEST_XML_MESSAGES_REPEAT), override_messages=True)

    assert len(definitions.messages) == 1
    assert 'test_message_extn' in [msg.name for msg in definitions.messages]

    message: parser.MessageDef = definitions.messages[0]
    assert len(message.fields) == 2
