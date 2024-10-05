import json
from enum import Enum

import pytest
from nasdaq_protocols.common import *


TEST_RECORD_FIELDS = [
    structures.Field('byte_field', types.Byte),
    structures.Field('short_field', types.Short),
    structures.Field('string_field', types.AsciiString),
]


class SampleTestRecord(Record):
    __test__ = False
    Fields = TEST_RECORD_FIELDS

    byte_field: int
    short_field: int
    string_field: str


class SampleTestRecordWithPresentBit(RecordWithPresentBit):
    __test__ = False
    Fields = TEST_RECORD_FIELDS

    byte_field: int
    short_field: int
    string_field: str


class SampleTestRecordInRecord(structures.RecordWithPresentBit):
    __test__ = False
    Fields = [
        structures.Field('record', SampleTestRecordWithPresentBit)
    ]

    record: SampleTestRecordWithPresentBit


class SampleTestArrayOfRecords(structures.RecordWithPresentBit):
    __test__ = False
    Fields = [
        structures.Field('records', Array(SampleTestRecordWithPresentBit))
    ]

    records: list[SampleTestRecordWithPresentBit]


class SampleTestMessage(structures.CommonMessage):
    BodyRecord = SampleTestRecord


def test__record__to_bytes():
    expected_bytes = b'\x02\x05\x00\x04\x00test'
    record = SampleTestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'

    len_, bytes_ = SampleTestRecord.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__from_bytes():
    record = SampleTestRecord.from_bytes(b'\x02\x05\x00\x04\x00test')[1]

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record_with_present_bit__to_bytes():
    expected_bytes = b'\x01\x02\x05\x00\x04\x00test'
    record = SampleTestRecordWithPresentBit()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'

    len_, bytes_ = SampleTestRecordWithPresentBit.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record_with_present_bit__from_bytes():
    record = SampleTestRecordWithPresentBit.from_bytes(b'\x01\x02\x05\x00\x04\x00test')[1]

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record___record_in_record__to_bytes():
    expected_bytes = b'\x01\x01\x02\x05\x00\x04\x00test'
    record = SampleTestRecordInRecord()
    record.record = SampleTestRecordWithPresentBit()
    record.record.byte_field = 2
    record.record.short_field = 5
    record.record.string_field = 'test'

    assert record.record.byte_field == 2
    assert record.record.short_field == 5
    assert record.record.string_field == 'test'

    len_, bytes_ = SampleTestRecordInRecord.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__record_in_record__from_bytes():
    record = SampleTestRecordInRecord.from_bytes(b'\x01\x01\x02\x05\x00\x04\x00test')[1]

    assert record.record.byte_field == 2
    assert record.record.short_field == 5
    assert record.record.string_field == 'test'


def test__record__array_of_records__to_bytes():
    expected_bytes = b'\x01\x02\x00' + (b'\x02\x05\x00\x04\x00test' * 2)
    record = SampleTestArrayOfRecords()
    record.records = [
        SampleTestRecordWithPresentBit(),
        SampleTestRecordWithPresentBit(),
    ]
    record.records[0].byte_field = 2
    record.records[0].short_field = 5
    record.records[0].string_field = 'test'
    record.records[1].byte_field = 2
    record.records[1].short_field = 5
    record.records[1].string_field = 'test'

    assert record.records[0].byte_field == 2
    assert record.records[0].short_field == 5
    assert record.records[0].string_field == 'test'
    assert record.records[1].byte_field == 2
    assert record.records[1].short_field == 5
    assert record.records[1].string_field == 'test'

    len_, bytes_ = SampleTestArrayOfRecords.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__array_of_records__from_bytes():
    record = SampleTestArrayOfRecords.from_bytes(b'\x01\x02\x00' + (b'\x02\x05\x00\x04\x00test' * 2))[1]

    assert record.records[0].byte_field == 2
    assert record.records[0].short_field == 5
    assert record.records[0].string_field == 'test'
    assert record.records[1].byte_field == 2
    assert record.records[1].short_field == 5
    assert record.records[1].string_field == 'test'


def test__record__equal():
    record1 = SampleTestRecord()
    record1.byte_field = 2
    record1.short_field = 5
    record1.string_field = 'test'

    record2 = SampleTestRecord()
    record2.byte_field = 2
    record2.short_field = 5
    record2.string_field = 'test'

    assert record1 == record2
    assert record1 != 1
    assert record1 != 'test'
    assert record1 != SampleTestRecordWithPresentBit()


def test__record__not_equal():
    record1 = SampleTestRecord()
    record1.byte_field = 2
    record1.short_field = 5
    record1.string_field = 'test'

    record2 = SampleTestRecord()
    record2.byte_field = 2
    record2.short_field = 5
    record2.string_field = 'test2'

    assert record1 != record2


def test__record__to_str():
    record = SampleTestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert (SampleTestRecord.to_str(record) ==
            str(record) ==
            "{'SampleTestRecord':{{'byte_field': 2, 'short_field': 5, 'string_field': 'test'}}}")


def test__record__is_record():
    assert Record.is_record(SampleTestRecord)


def test__record__create_with_all_values():
    values = {
        'byte_field': 2,
        'short_field': 5,
        'string_field': 'test'
    }
    record = SampleTestRecord(values)

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record__nested_record__default_values_initialised():
    values = {
    }
    record = SampleTestRecordInRecord(values)

    assert record.record.byte_field == 0
    assert record.record.short_field == 0
    assert record.record.string_field == ''


def test__record__from_str__not_implemented():
    with pytest.raises(NotImplementedError):
        SampleTestRecord.from_str('test')


def test__record__enum_type_field():
    class TestEnum(Enum):
        A = 1
        B = 2

    record = SampleTestRecord()
    record.byte_field = TestEnum.A
    record.short_field = TestEnum.B
    record.string_field = 'test'

    assert record.byte_field == 1
    assert record.short_field == 2


def test__record__invalid_type__exception_is_raised():
    record = SampleTestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    with pytest.raises(ValueError):
        record.string_field = 3

    with pytest.raises(ValueError):
        record_in_record = SampleTestRecordInRecord()
        record_in_record.record = record


def test__record_with_present_bit__get_value():
    record = SampleTestRecordWithPresentBit()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    record_in_record = SampleTestRecordInRecord()
    record_in_record.record = record

    array_of_records = SampleTestArrayOfRecords()
    array_of_records.records = [record, record]

    assert Record.get_value(record_in_record) == {
        'SampleTestRecordInRecord': {
            'record': {
                'SampleTestRecordWithPresentBit': {
                    'byte_field': 2,
                    'short_field': 5,
                    'string_field': 'test'
                }
            }
        }
    }

    assert Record.get_value(array_of_records) == {
        'SampleTestArrayOfRecords': {
            'records': [
                {
                    'SampleTestRecordWithPresentBit': {
                        'byte_field': 2,
                        'short_field': 5,
                        'string_field': 'test'
                    }
                },
                {
                    'SampleTestRecordWithPresentBit': {
                        'byte_field': 2,
                        'short_field': 5,
                        'string_field': 'test'
                    }
                }
            ]
        }
    }


def test__array__from_str__not_implemented():
    with pytest.raises(NotImplementedError):
        Array.from_str('test')


def test__array__to_str__not_implemented():
    with pytest.raises(NotImplementedError):
        Array.to_str('test')


def test__array__basic_types__to_bytes():
    array_of_chars = Array(types.CharAscii)
    input_ = 'abcde'
    expected_op = (7, b'\x05\x00abcde')

    assert array_of_chars.to_bytes(input_) == expected_op


def test__array__basic_types__from_bytes():
    array_of_chars = Array(types.CharAscii)
    input_ = b'\x05\x00abcde'
    expected_op = (7, ['a', 'b', 'c', 'd', 'e'])

    assert array_of_chars.from_bytes(input_) == expected_op


def test__record_with_present_bit__empty_record__to_bytes():
    assert SampleTestRecordWithPresentBit.to_bytes(None) == (1, b'\x00')
    assert SampleTestRecordWithPresentBit.to_bytes(SampleTestRecordWithPresentBit()) == (1, b'\x00')


def test__record_with_present_bit__empty_record2__from_bytes():
    assert SampleTestRecordWithPresentBit.from_bytes(b'\x00') == (1, None)


def test__common_message__as_collection():
    message = SampleTestMessage()
    data = {
        'message': 'SampleTestMessage[None]',
        'body': {}
    }
    assert str(message) == json.dumps(data, indent=2)
