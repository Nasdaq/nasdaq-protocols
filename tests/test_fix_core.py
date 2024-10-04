from operator import index

import pytest
from .fix_messages import *


def test__to_bytes__field__invalid_format():
    with pytest.raises(ValueError):
        Field_1_Int.from_bytes(b'somebytes')


def test__to_bytes__field__bytes_are_expected():
    expected_bytes = b'1=10'

    assert Field_1_Int(10).to_bytes() == (4, expected_bytes)


def test__from_bytes__field__field_is_deserialized():
    expected_field = Field_1_Int(10)

    assert Field_1_Int.from_bytes(b'1=10') == (4, expected_field)
    assert Field_1_Int.from_bytes(b'1=10' + fix.SOH) == (5, expected_field)


def test__from_value__field__field_is_constructed():
    assert Field_1_Int.from_value(10) == Field_1_Int(10)
    assert Field_1_Int.from_value(Field_1_Int(10)) == Field_1_Int(10)


def test__from_value__field__invalid_type():
    with pytest.raises(TypeError):
        Field_1_Int.from_value('a')


def test__from_tag_value__field__tag_value_returned():
    assert fix.Field.from_tag_value(1, 10) == Field_1_Int(10)
    assert fix.Field.from_tag_value('Field_1_Int', 10) == Field_1_Int(10)


def test__index__field__value_is_returned():
    assert index(Field_1_Int(10)) == 10

    test_data = ['one', 'two']
    assert test_data[Field_1_Int(1)] == 'two'


def test__len__field__length_of_value_is_returned():
    assert len(Field_2_Str('test')) == 4


def test__len__int_field__exception_is_thrown():
    with pytest.raises(TypeError):
        len(Field_1_Int(1))


def test__hash__field__hash_of_value_returned():
    assert hash(Field_1_Int(10)) == 10
    assert hash(Field_2_Str('test')) == hash('test')


def test__eq__field__equals():
    assert Field_1_Int(10) == Field_1_Int(10)
    assert Field_1_Int(10) == 10


def test__eq__field__not_equals():
    assert Field_1_Int(10) != Field_11_Int(10)
    assert Field_1_Int(10) != Field_1_Int(20)
    assert Field_1_Int(10) != 20
    assert Field_1_Int(10) != Field_2_Str('test')


def test__repr__int_field():
    assert repr(Field_1_Int(10)) == 'Field_1_Int[1]: 10'


def test__repr__str_field():
    assert repr(Field_2_Str('test')) == "Field_2_Str[2]: 'test'"


def test__from_bytes__segment_ends_without_SOH__bytes_are_serialized():
    bytes_ = b'1=10' + fix.SOH + b'2=test' + fix.SOH + b'11=100'

    len_, segment = DataSegment_1.from_bytes(bytes_)

    assert len_ == len(bytes_)
    assert isinstance(segment, DataSegment_1)
    assert segment.Field_1_Int == 10
    assert segment.Field_2_Str == 'test'
    assert segment.Field_11_Int == 100


def test__from_bytes__segment_ends_with_SOH__bytes_are_serialized():
    bytes_ = b'1=10' + fix.SOH + b'2=test' + fix.SOH + b'11=100' + fix.SOH

    len_, segment = DataSegment_1.from_bytes(bytes_)

    assert len_ == len(bytes_)
    assert isinstance(segment, DataSegment_1)
    assert segment.Field_1_Int == 10
    assert segment.Field_2_Str == 'test'
    assert segment.Field_11_Int == 100


def test__from_bytes__segment_repeats_tag__bytes_are_serialized():
    bytes_ = b'1=10' + fix.SOH + b'2=test' + fix.SOH + b'11=100' + fix.SOH

    len_, segment = DataSegment_1.from_bytes(bytes_ + bytes_)

    assert len_ == len(bytes_)
    assert isinstance(segment, DataSegment_1)
    assert segment.Field_1_Int == 10
    assert segment.Field_2_Str == 'test'
    assert segment.Field_11_Int == 100


def test__from_bytes__segment_contains_unknown_tag__bytes_are_serialized():
    bytes_ = b'1=10' + fix.SOH + b'2=test' + fix.SOH + b'11=100' + fix.SOH

    len_, segment = DataSegment_1.from_bytes(bytes_ + b'999=1000')

    assert len_ == len(bytes_)
    assert isinstance(segment, DataSegment_1)
    assert segment.Field_1_Int == 10
    assert segment.Field_2_Str == 'test'
    assert segment.Field_11_Int == 100


def test__to_bytes__segment__segment_is_serialized():
    expected_bytes = b'1=10' + fix.SOH + b'2=test' + fix.SOH + b'11=100'

    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'
    segment.Field_11_Int = 100

    assert segment.to_bytes() == (len(expected_bytes), expected_bytes)


def test__contains__segment__tag_presence_is_checked():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'

    assert 1 in segment
    assert 'Field_1_Int' in segment

    assert 2 in segment
    assert 'Field_2_Str' in segment

    assert 11 not in segment
    assert 'Field_11_Int' not in segment


def test__contains__segment__check_tag_presence_in_segment():
    assert DataSegment_1.contains(1) is True
    assert DataSegment_1.contains('Field_1_Int') is True

    assert DataSegment_1.contains(2) is True
    assert DataSegment_1.contains('Field_2_Str') is True

    assert DataSegment_1.contains(11) is True
    assert DataSegment_1.contains('Field_11_Int') is True

    assert DataSegment_1.contains(1001) is False


def test__validate__segment__all_mandatory_fields_are_present():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'

    # test Validate does not throw exception
    segment.validate()


def test__validate__segment__missing_mandatory_field():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_11_Int = 100

    with pytest.raises(ValueError):
        segment.validate()


def test__validate__segment__missing_mandatory_fields():
    segment = DataSegment_1()
    segment.Field_11_Int = 100

    with pytest.raises(ValueError):
        segment.validate()


def test__len__segment__returns_count_of_fields_in_segment():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'
    segment.Field_11_Int = 11

    assert len(segment) == 3


def test__from_value__segment__equal_objects_are_compared():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'
    segment.Field_11_Int = 11

    assert DataSegment_1.from_value(segment) == segment


def test__from_value__values__equal_objects_are_compared():
    segment = DataSegment_1()
    segment.Field_1_Int = 10
    segment.Field_2_Str = 'test'
    segment.Field_11_Int = 11

    assert DataSegment_1.from_value({1: 10, 2: 'test', 11: 11}) == segment


def test__from_value__unsupported_values__exception_is_raised():
    with pytest.raises(TypeError):
        assert DataSegment_1.from_value(b'asda')


def test__init__group_container__raises_exception_when_created_with_wrong_types():
    with pytest.raises(TypeError):
        GroupContainer_1(values=[1])


def test_from_bytes__group_container_with_one_group__container_is_deserialized():
    bytes_ = b'11=1' + fix.SOH + b'1=10' + fix.SOH + b'2=test'

    length, container = GroupContainer_1.from_bytes(bytes_)

    assert length == len(bytes_)
    assert len(container) == 1

    group = container[0]
    assert isinstance(group, Group_1)
    assert group.Field_1_Int == 10
    assert group.Field_2_Str == 'test'


def test_from_bytes__group_container_with_two_groups__container_is_deserialized():
    group_1_bytes = b'1=10' + fix.SOH + b'2=test'
    group_2_bytes = b'1=20' + fix.SOH + b'2=test1'
    bytes_ = b'11=2' + fix.SOH + group_1_bytes + fix.SOH + group_2_bytes

    length, container = GroupContainer_1.from_bytes(bytes_)

    assert length == len(bytes_)
    assert len(container) == 2

    group = container[0]
    assert isinstance(group, Group_1)
    assert group.Field_1_Int == 10
    assert group.Field_2_Str == 'test'

    group = container[1]
    assert isinstance(group, Group_1)
    assert group.Field_1_Int == 20
    assert group.Field_2_Str == 'test1'


def test_from_bytes__group_container__unknown_tag_present_container_is_deserialized():
    container_bytes = b'11=1' + fix.SOH + b'1=10' + fix.SOH + b'2=test'
    bytes_ = container_bytes + fix.SOH + b'788=12'

    length, container = GroupContainer_1.from_bytes(bytes_)

    assert length == len(container_bytes) + 1
    assert len(container) == 1

    group = container[0]
    assert isinstance(group, Group_1)
    assert group.Field_1_Int == 10
    assert group.Field_2_Str == 'test'


def test__from_bytes__group_container__invalid_group_count__raises_exception():
    bytes_ = b'11=2' + fix.SOH + b'1=10' + fix.SOH + b'2=test'

    with pytest.raises(ValueError):
        GroupContainer_1.from_bytes(bytes_)


def test__to_bytes__group_container_with_one_group__container_is_deserialized():
    expected_bytes = b'11=1' + fix.SOH + b'1=10' + fix.SOH + b'2=test'

    group = Group_1()
    group.Field_1_Int = 10
    group.Field_2_Str = 'test'

    group_container = GroupContainer_1(values=[group])

    assert len(group_container) == 1
    assert group_container.to_bytes() == (len(expected_bytes), expected_bytes)


def test__to_bytes__group_container_with_reordered_fields__container_is_deserialized_as_per_order():
    expected_bytes = b'11=1' + fix.SOH + b'1=10' + fix.SOH + b'2=test'

    group = Group_1()
    group.Field_2_Str = 'test'
    group.Field_1_Int = 10

    group_container = GroupContainer_1(values=[group])

    assert len(group_container) == 1
    assert group_container.to_bytes() == (len(expected_bytes), expected_bytes)


def test__to_bytes__group_container_with_two_group__container_is_deserialized():
    group_1_bytes = b'1=10' + fix.SOH + b'2=test'
    group_2_bytes = b'1=20' + fix.SOH + b'2=test1'
    expected_bytes = b'11=2' + fix.SOH + group_1_bytes + fix.SOH + group_2_bytes

    group1 = Group_1()
    group1.Field_1_Int = 10
    group1.Field_2_Str = 'test'

    group2 = Group_1()
    group2.Field_1_Int = 20
    group2.Field_2_Str = 'test1'

    group_container = GroupContainer_1(count=2)
    group_container[0] = group1
    group_container[1] = group2

    assert len(group_container) == 2
    assert group_container.to_bytes() == (len(expected_bytes), expected_bytes)


def test__from_value__group_container__groups_are_passed_as_values():
    group1 = Group_1()
    group1.Field_1_Int = 10
    group1.Field_2_Str = 'test'

    group2 = Group_1()
    group2.Field_1_Int = 20
    group2.Field_2_Str = 'test1'

    group_container = GroupContainer_1.from_value([group1, group2])

    assert len(group_container) == 2
    assert group_container[0] == group1
    assert group_container[1] == group2


def test__from_value__group_container__dict_passed_as_value():
    group1 = Group_1()
    group1.Field_1_Int = 10
    group1.Field_2_Str = 'test'

    group2 = Group_1()
    group2.Field_1_Int = 20
    group2.Field_2_Str = 'test1'

    group_container = GroupContainer_1.from_value([
        {
            1: 10,
            2: 'test'
        },
        {
            1: 20,
            2: 'test1'
        }
    ])

    assert len(group_container) == 2
    assert group_container[0] == group1
    assert group_container[1] == group2


def test__equals__group_container__containers_are_equal():
    container1 = GroupContainer_1.from_value([
        {
            1: 10,
            2: 'test'
        },
    ])
    container2 = GroupContainer_1.from_value([
        {
            1: 10,
            2: 'test'
        },
    ])
    assert container1 == container2


def test__equals__group_container__containers_are_not_equal():
    container1 = GroupContainer_1.from_value([
        {
            1: 10,
            2: 'test'
        },
    ])
    container2 = GroupContainer_1.from_value([
        {
            1: 20,
            2: 'test1'
        },
    ])
    assert container1 != container2


def test__equals__group_container__different_value_types_containers_are_not_equal():
    container1 = GroupContainer_1.from_value([
        {
            1: 10,
            2: 'test'
        },
    ])
    data = [
        {
            1: 20,
            2: 'test1'
        },
    ]
    assert container1 != data


def test__to_bytes__message__empty_message():
    message = Message_1()

    assert message.to_bytes() == (1, fix.SOH)


def test__to_bytes__message__message_is_serialized():
    expected_bytes = b'8=begin\x019=10\x0135=L\x011=2\x012=body\x0110=30\x01'
    header = DataSegment_Header.from_value({
        8: "begin",
        9: 10,
        35: 'L'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body'
    })
    trailer = DataSegment_Trailer.from_value({
        10: '30'
    })
    message = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })
    assert message.to_bytes() == (len(expected_bytes), expected_bytes)


def test__to_bytes__message_constructed_using_from_value__message_is_serialized():
    expected_bytes = b'8=test\x019=1\x0135=Hello\x011=2\x012=body\x0110=3\x01'
    header = DataSegment_Header.from_value({
        8: "test",
        9: 1,
        35: "Hello"
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body'
    })
    trailer = DataSegment_Trailer.from_value({
        10: '3',
    })
    message = Message_1.from_value({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })
    assert message.to_bytes() == (len(expected_bytes), expected_bytes)


def test__to_bytes__message_constructed_fully_using_dict__message_is_serialized():
    expected_bytes = b'8=test\x019=1\x0135=Hello\x011=2\x012=body\x0110=3\x01'
    message = Message_1(
        {
            fix.MessageSegments.HEADER: {
                8: "test",
                "BodyLength": 1,
                35: "Hello",
            },
            fix.MessageSegments.TRAILER: {
                10: '3',
            },
            fix.MessageSegments.BODY: {
                1: 2,
                2: 'body'
            }
        }
    )
    assert message.to_bytes() == (len(expected_bytes), expected_bytes)


def test__as_collection__message__entire_message_is_returned_as_collection():
    header = DataSegment_Header.from_value({
        8: 'beginstring',
        9: 50,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })

    assert message.as_collection() == {
        'Header': {
            8: 'beginstring',
            9: 50,
            35: 'M'
        },
        'Body': {
            1: 2,
            2: 'body',
            22: [
                {
                    1: 21,
                    2: 'body_inner'
                }
            ]
        },
        'Trailer': {
            10: '100'
        }
    }


def test__getattr__message__able_to_resolve_segment_fields():
    message = Message_1()
    assert message.Body.Field_1_Int == 0

    # Body fields can be directly accessed using message.
    message.Field_1_Int = 10
    assert message.Body.Field_1_Int == 10
    assert message.Trailer.Field_1_Int == 0
    assert message.GroupContainer_2 is None


def test__getattr__message__fall_back_to_object_attributes_on_non_segment_fields():
    message = Message_1()

    data = message.data

    assert isinstance(data, dict)


def test__equals__message__messages_are_equal():
    header = DataSegment_Header.from_value({
        8: 'beginstring',
        9: 50,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message1 = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })

    message2 = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })

    assert message1 == message2
    assert message1 is not message2


def test__equals__message__messages_are_not_equal():
    header = DataSegment_Header.from_value({
        8: 'beginstring',
        9: 50,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message1 = Message_1({
        fix.MessageSegments.HEADER: DataSegment_Header.from_value(header),
        fix.MessageSegments.BODY: DataSegment_1.from_value(body),
        fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value(trailer)
    })

    message2 = Message_1({
        fix.MessageSegments.HEADER: DataSegment_Header.from_value(header),
        fix.MessageSegments.BODY: DataSegment_1.from_value(body),
        fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value(trailer)
    })
    message2.Field_1_Int = 100
    message2.Field_2_Str = 'message2'

    assert message1 != message2
    assert message1 is not message2


def test__equals__message__non_related_object_messages_are_not_equal():
    header = DataSegment_Header.from_value({
        8: 'beginstring',
        9: 50,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message1 = Message_1({
        fix.MessageSegments.HEADER: DataSegment_Header.from_value(header),
        fix.MessageSegments.BODY: DataSegment_1.from_value(body),
        fix.MessageSegments.TRAILER: DataSegment_Trailer.from_value(trailer)
    })

    assert message1 != 100


def test__from_bytes__message__use_base_message_class_to_deserialize():
    header = DataSegment_Header.from_value({
        8: 'FIXT1.1',
        9: 37,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message1 = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })

    len_, bytes_ = message1.to_bytes()

    deserialized_len, message2 = fix.Message.from_bytes(bytes_)

    assert len_ == deserialized_len
    assert message1 == message2


def test__is_logout__message():
    class Logout(fix.Message, Name='Logout', Type='5', Category='B', HeaderCls=DataSegment_1,
                    BodyCls=DataSegment_1, TrailerCls=DataSegment_1):
        Header: DataSegment_1
        Body: DataSegment_1
        Trailer: DataSegment_1

    logout = Logout()

    assert logout.is_logout()
    assert not logout.is_heartbeat()


def test__is_heartbeat__message():
    heartbeat = Heartbeat()

    assert heartbeat.is_heartbeat()
    assert not heartbeat.is_logout()


def test__str__message__message_is_pretty_printed():
    header = DataSegment_Header.from_value({
        8: 'beginstring',
        9: 50,
        35: 'M'
    })
    body = DataSegment_1.from_value({
        1: 2,
        2: 'body',
        22: [
            {
                1: 21,
                2: 'body_inner'
            }
        ]
    })
    trailer = DataSegment_Trailer.from_value({
        10: '100'
    })
    message1 = Message_1({
        fix.MessageSegments.HEADER: header,
        fix.MessageSegments.BODY: body,
        fix.MessageSegments.TRAILER: trailer
    })

    str_ = repr(message1)

    assert 'Header' in str_
    assert 'Body' in str_
    assert 'Trailer' in str_


def test__validate__message__mandatory_fields_missing():
    message1 = Message_1()

    with pytest.raises(ValueError):
        message1.validate()