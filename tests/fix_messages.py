from nasdaq_protocols import fix


class Field_1_Int(fix.Field, Tag=1, Name="Field_1_Int", Type=fix.FixInt):
    ...


class Field_11_Int(fix.Field, Tag=11, Name="Field_11_Int", Type=fix.FixInt):
    ...


class Field_2_Str(fix.Field, Tag=2, Name="Field_2_Str", Type=fix.FixString):
    ...


class Field_22_Int(fix.Field, Tag=22, Name="Field_22_Int", Type=fix.FixInt):
    ...


class MsgType(fix.Field, Tag=35, Name="MsgType", Type=fix.FixString):
    ...


class BeginString(fix.Field, Tag=8, Name="BeginString", Type=fix.FixString, Values={}):
    ...


class BodyLength(fix.Field, Tag=9, Name="BodyLength", Type=fix.FixInt, Values={}):
    ...


class CheckSum(fix.Field, Tag=10, Name="CheckSum", Type=fix.FixString, Values={}):
    ...


class MsgSeqNum(fix.Field, Tag="34", Name="MsgSeqNum", Type=fix.FixInt):
    Values = None


class SenderSubID(fix.Field, Tag="50", Name="SenderSubID", Type=fix.FixString):
    Values = None


class TargetCompID(fix.Field, Tag="56", Name="TargetCompID", Type=fix.FixString):
    Values = None


class SendingTime(fix.Field, Tag="52", Name="SendingTime", Type=fix.FixUTCTimeStamp):
    Values = None


class SenderCompID(fix.Field, Tag="49", Name="SenderCompID", Type=fix.FixString):
    Values = None


class TargetSubID(fix.Field, Tag="57", Name="TargetSubID", Type=fix.FixString):
    Values = None


class Username(fix.Field, Tag="553", Name="Username", Type=fix.FixString):
    Values = None


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
        fix.Entry(MsgType, False)
    ]

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2
    MsgType: str


class DataSegment_Header(fix.DataSegment):
    Entries = [
        fix.Entry(BeginString, True),
        fix.Entry(BodyLength, True),
        fix.Entry(MsgType, False),
    ]

    BeginString: str
    BodyLength: int
    MsgType: str


class DataSegment_Trailer(fix.DataSegment):
    Entries = [
        fix.Entry(CheckSum, True),
        fix.Entry(Field_1_Int, False)
    ]

    CheckSum: int
    Field_1_Int: int


class Message_1(fix.Message,
                Name='Message_1',
                Type='M',
                Category='B',
                HeaderCls=DataSegment_Header,
                BodyCls=DataSegment_1,
                TrailerCls=DataSegment_Trailer):
    Header: DataSegment_Header
    Body: DataSegment_1
    Trailer: DataSegment_Trailer

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2


class Message_5(fix.Message,
                Name='Message_5',
                Type='5',
                Category='B',
                HeaderCls=DataSegment_Header,
                BodyCls=DataSegment_1,
                TrailerCls=DataSegment_Trailer):
    Header: DataSegment_Header
    Body: DataSegment_1
    Trailer: DataSegment_Trailer

    Field_1_Int: int
    Field_2_Str: str
    Field_11_Int: int
    GroupContainer_2: GroupContainer_2


class Header(fix.DataSegment):
    Entries = [
        fix.Entry(BeginString, True),
        fix.Entry(BodyLength, True),
        fix.Entry(MsgType, True),
        fix.Entry(SenderCompID, True),
        fix.Entry(TargetCompID, True),
        fix.Entry(MsgSeqNum, True),
        fix.Entry(SenderSubID, False),
        fix.Entry(TargetSubID, False),
        fix.Entry(SendingTime, True),
    ]


class Trailer(fix.DataSegment):
    Entries = [
        fix.Entry(CheckSum, True),
    ]


class Body(fix.DataSegment):
    Entries = [
        fix.Entry(Username, False),
    ]


class Heartbeat(fix.Message,
                Name="Heartbeat",
                Type="0",
                Category="Session",
                HeaderCls=Header,
                BodyCls=Body,
                TrailerCls=Trailer):
    ...


class Login(fix.Message,
            Name='Login',
            Type='L',
            Category='L',
            HeaderCls=Header,
            BodyCls=Body,
            TrailerCls=Trailer
            ):
    ...


class Nope(fix.Message,
           Name='Nope',
           Type='N',
           Category='N',
           HeaderCls=Header,
           BodyCls=Body,
           TrailerCls=Trailer
           ):
    ...
