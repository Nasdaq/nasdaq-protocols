from nasdaq_protocols import fix


class Field_1_Int(fix.Field, Tag=1, Name="Field_1_Int", Type=fix.FixInt):
    ...


class Field_11_Int(fix.Field, Tag=11, Name="Field_11_Int", Type=fix.FixInt):
    ...


class Field_2_Str(fix.Field, Tag=2, Name="Field_2_Str", Type=fix.FixString):
    ...


class Field_22_Int(fix.Field, Tag=22, Name="Field_22_Int", Type=fix.FixInt):
    ...


class Field_35_Str(fix.Field, Tag=35, Name="Field_35_Str", Type=fix.FixString):
    ...


class Field_8_Str(fix.Field, Tag=8, Name="Field_8_Str", Type=fix.FixString, Values={}):
    ...


class Field_9_Int(fix.Field, Tag=9, Name="Field_9_Int", Type=fix.FixInt, Values={}):
    ...


class Field_10_Int(fix.Field, Tag=10, Name="Field_10_Int", Type=fix.FixInt, Values={}):
    ...


class Group_1(fix.Group):
    Entries = [
        fix.Entry(Field_1_Int, True),
        fix.Entry(Field_2_Str, False),
    ]

    Field_1_Int: int
    Field_2_Str: str


class GroupContainer_1(fix.GroupContainer, CountCls=Field_11_Int, GroupCls=Group_1):
    def __getitem__(self, idx) -> Group_1:
        return super(GroupContainer_1, self).__getitem__(idx)


class Group_2(fix.Group):
    Entries = [
        fix.Entry(Field_1_Int, True),
        fix.Entry(Field_2_Str, False),
    ]

    Field_1_Int: int
    Field_2_Str: str


class GroupContainer_2(fix.GroupContainer, CountCls=Field_22_Int, GroupCls=Group_2):
    def __getitem__(self, idx) -> Group_1:
        return super(GroupContainer_2, self).__getitem__(idx)


class DataSegment_1(fix.DataSegment):
    Entries = [
        fix.Entry(Field_1_Int, True),
        fix.Entry(Field_2_Str, True),
        fix.Entry(Field_11_Int, False),
        fix.Entry(GroupContainer_2, False),
        fix.Entry(Field_35_Str, False)
    ]

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2
    Field_35_Str: str


class DataSegment_Header(fix.DataSegment):
    Entries = [
        fix.Entry(Field_8_Str, True),
        fix.Entry(Field_9_Int, True),
        fix.Entry(Field_35_Str, False),
    ]

    Field_8_Str: str
    Field_9_Int: int
    Field_35_Str: str


class DataSegment_Trailer(fix.DataSegment):
    Entries = [
        fix.Entry(Field_10_Int, True),
        fix.Entry(Field_1_Int, False)
    ]

    Field_10_Int: int
    Field_1_Int: int


class Message_1(fix.Message, Name='Message_1', Type='M', Category='B', HeaderCls=DataSegment_Header, BodyCls=DataSegment_1, TrailerCls=DataSegment_Trailer):
    Header: DataSegment_Header
    Body: DataSegment_1
    Trailer: DataSegment_Trailer

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2


class Message_5(fix.Message, Name='Message_5', Type='5', Category='B', HeaderCls=DataSegment_Header, BodyCls=DataSegment_1, TrailerCls=DataSegment_Trailer):
    Header: DataSegment_Header
    Body: DataSegment_1
    Trailer: DataSegment_Trailer

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2