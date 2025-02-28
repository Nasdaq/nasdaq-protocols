TEST_XML_EMPTY_ENUMS_ROOT = """
<root>
    <enums-root/>
    <fielddef-root/>
</root>
"""


TEST_XML_ENUMS = """
<root>
    <enums-root>
        <enum id="test_enum" type="uint_8">
            <value name="enum_1" description="enum_1_desc">1</value>
            <value name="enum_2" description="enum_2_desc">2</value>
        </enum>
    </enums-root>
</root>
"""


TEST_XML_RECORDS = """
<root>
    <enums-root>
        <enum id="test_enum" type="char_ascii">
            <value name="enum_1" description="enum_1_desc">1</value>
        </enum>
    </enums-root>
    <fielddef-root>
        <field name="int_field1_def" type="uint_4"/>
        <field name="int_field2_def" type="uint_4"/>
    </fielddef-root>
    <records-root>
        <record id="test_record">
            <fields>
                <field name="int_field1" type="uint_8" default="0"/>
                <field name="array_field" array="single" length="5" type="uint_2"/>
                <field name="override_name_for_field1_def" def="int_field1_def"/>
                <field def="int_field2_def"/>
                <field name="enum_field" type="enum:test_enum"/>
            </fields>
        </record>
    </records-root>
</root>
"""


TEST_XML_MESSAGES = """
<root>
    <enums-root>
        <enum id="test_enum" type="char_ascii">
            <value name="enum_1" description="enum_1_desc">1</value>
        </enum>
    </enums-root>
    <fielddef-root>
        <field name="int_field1_def" type="uint_4"/>
        <field name="int_field2_def" type="uint_4"/>
    </fielddef-root>
    <records-root>
        <record id="test_record">
            <fields>
                <field name="int_field1" type="uint_8" default="0"/>
                <field name="array_field" array="single" length="5" type="uint_2"/>
                <field name="override_name_for_field1_def" def="int_field1_def"/>
                <field def="int_field2_def"/>
                <field name="enum_field" type="enum:test_enum"/>
            </fields>
        </record>
    </records-root>
    <messages-root>
        <message id="test_message" message-id="1" message-group="test_group" direction="incoming">
            <fields>
                <field name="direct_int_field1" type="uint_4"/>
                <field name="record_field" type="record:test_record"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_XML_MESSAGES_1 = """
<root>
    <enums-root>
        <enum id="test_enum" type="char_ascii">
            <value name="enum_1" description="enum_1_desc">1</value>
            <value name="enum_2" description="enum_2_desc">2</value>
        </enum>
        <enum id="test_enum2" type="uint_8">
            <value name="enum_1" description="enum_1_desc">1</value>
            <value name="enum_2" description="enum_2_desc">2</value>
        </enum>
        <enum id="test_enum3" type="uint_8">
            <value name="enum_1" description="enum_1_desc">1</value>
            <value name="enum_2" description="enum_2_desc">2</value>
        </enum>
    </enums-root>
    <fielddef-root>
        <field name="int_field1_def" type="uint_8"/>
        <field name="int_field2_def" type="uint_8"/>
    </fielddef-root>
    <records-root>
        <record id="test_record">
            <fields>
                <field name="int_field1" type="uint_8" default="0"/>
                <field name="override_name_for_field1_def" def="int_field1_def"/>
                <field def="int_field2_def"/>
                <field name="enum_field" type="enum:test_enum"/>
            </fields>
        </record>
    </records-root>
    <messages-root>
        <message id="test_message" message-id="1" message-group="2" direction="incoming">
            <fields>
                <field name="msg_field1" type="uint_4" default="0"/>
                <field name="enum_field" type="enum:test_enum"/>
                <field def="int_field1_def" />
                <field name="somerecord" type="record:test_record"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_XML_OUCH_MESSAGE = """
<root>
    <messages-root>
        <message id="TestMessage1" message-id="1" direction="incoming">
            <fields>
                <field name="field1" type="int_8_be"/>
                <field name="field2" type="char_iso-8859-1"/>
                <field name="field3" type="str_iso-8859-1_n" length="16"/>
            </fields>
        </message>
        <message id="TestMessage2" message-id="2" direction="outgoing">
            <fields>
                <field name="field1_1" type="int_8_be"/>
                <field name="field2_1" type="char_iso-8859-1"/>
                <field name="field3_1" type="str_iso-8859-1_n" length="16"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_XML_ITCH_MESSAGE = """
<root>
    <messages-root>
        <message id="TestMessage1" message-id="1" direction="outgoing">
            <fields>
                <field name="field1" type="int_8_be"/>
                <field name="field2" type="char_iso-8859-1"/>
                <field name="field3" type="str_iso-8859-1_n" length="16"/>
            </fields>
        </message>
        <message id="TestMessage2" message-id="2" direction="outgoing">
            <fields>
                <field name="field1_1" type="int_8_be"/>
                <field name="field2_1" type="char_iso-8859-1"/>
                <field name="field3_1" type="str_iso-8859-1_n" length="16"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_XML_MESSAGES_REPEAT = """
<root>
    <enums-root>
    </enums-root>
    <fielddef-root>
    </fielddef-root>
    <records-root>
    </records-root>
    <messages-root>
        <message id="test_message" message-id="1" message-group="2" direction="incoming">
            <fields>
                <field name="msg_field1" type="uint_4" default="0"/>
            </fields>
        </message>
        <message id="test_message_extn" message-id="1" message-group="2" direction="incoming">
            <fields>
                <field name="msg_field1" type="uint_4" default="0"/>
                <field name="msg_field2" type="uint_4" default="0"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_FIX_44_XML = """
<fix major="4" minor="4" servicepack="0">
    <header>
        <field name="BeginString" required="Y"/>
        <field name="BodyLength" required="N"/>
    </header>
    <trailer>
        <field name="CheckSum" required="Y"/>
    </trailer>
    <messages>
        <message name="Logon" msgtype="A" msgcat="Session">
            <field name="HeartBtInt" required="Y"/>
            <component name="InstrmtLegGrp" required="Y"/>
            <group name="NoStreams" required="Y">
                <component name="Instrument" required="Y"/>
            </group>
        </message>
    </messages>
    <components>
        <component name="InstrmtLegGrp">
            <field name="PossResend" required="N"/>
            <field name="QuoteStatus" required="N"/>
        </component>
        <component name="GroupOfComponents">
            <group name="NoLegs" required="N">
                <component name="InstrmtLegGrp" required="Y"/>
            </group>
            <group name="NoStreams" required="Y">
                <component name="Instrument" required="Y"/>
            </group>
        </component>
        <component name="Instrument">
            <field name="PossResend" required="Y"/>
            <field name="QuoteStatus" required="Y"/>
        </component>
        <component name="InstrumentExtensionNoInstrAttribSubGroup">
            <field name="PossResend" required="Y"/>
            <field name="QuoteStatus" required="N"/>
        </component>
    </components>
    <fields>
        <field number="108" name="HeartBtInt" type="INT" />
        <field number="10" name="CheckSum" type="STRING" />
        <field number="8" name="BeginString" type="STRING" />
        <field number="9" name="BodyLength" type="LENGTH" />
        <field number="35" name="MsgType" type="STRING" >
            <value enum="0" description="Heartbeat" />
            <value enum="1" description="Logout" />
        </field>
        <field number="97" name="PossResend" type="BOOLEAN" >
            <value enum="N" description="OrigTrans" />
            <value enum="Y" description="PossResend" />
        </field>
        <field number="297" name="QuoteStatus" type="INT" >
            <value enum="0" description="Accpt" />
            <value enum="1" description="CxlSym" />
            <value enum="10" description="Pending" />
        </field>
        <field number="555" name="NoLegs" type="NUMINGROUP" />
        <field number="40049" name="NoStreams" type="NUMINGROUP" />
    </fields>
</fix>
"""


TEST_SQF_MESSAGES = """
<root>
    <enums-root/>
    <fielddef-root>
        <field name="instrumentId" type="uint_8"/>
        <field name="price" type="uint_8"/>
        <field name="quantity" type="uint_8"/>
        <field name="timestamp" type="uint_8"/>
        <field name="someInfo" type="str_iso-8859-1_n" length="32"/>
    </fielddef-root>
    <records-root>
        <record id="Quote">
            <fields>
                <field def="instrumentId"/>
                <field name="bidPrice" def="price"/>
                <field name="askPrice" def="price"/>
                <field name="bidQuantity" def="quantity"/>
                <field name="askQuantity" def="quantity"/>
            </fields>
        </record>
    </records-root>
    <messages-root>
        <message id="QuoteMessage" message-id="1" direction="incoming">
            <fields>
                <field def="timestamp"/>
                <field def="someInfo"/>
                <field name="quotes" type="record:Quote" array="true" endian="big"/>
            </fields>
        </message>
    </messages-root>
</root>
"""


TEST_ASN1_SPEC = """
MyShopPurchaseOrders DEFINITIONS AUTOMATIC TAGS ::= BEGIN

OrderType ::= ENUMERATED
{
    retail(0),
    wholesale(1)
}

MyCompanyAutomation ::= CHOICE {
  purchaseOrder  [0] PurchaseOrder,
  purchaseQuote  [1] PurchaseQuote
}


PurchaseQuote ::= SEQUENCE {
    quoteId    INTEGER,
    itemName   VisibleString (SIZE (1..50)),
    itemPrice  INTEGER (1..99999),
    itemQty    INTEGER (1..100),
    extension BITSTRING
}

PurchaseOrder ::= SEQUENCE {
  dateOfOrder NumericString,
  customer    CustomerInfo,
  orderType   OrderType,
  items       ListOfItems
}

CustomerInfo ::= SEQUENCE {
  companyName    VisibleString (SIZE (3..50)),
  billingAddress Address,
  contactPhone   NumericString (SIZE (7..12))
}

Address::= SEQUENCE {
  street  VisibleString (SIZE (5 .. 50)) OPTIONAL,
  city    VisibleString (SIZE (2..30)),
  state   VisibleString (SIZE(2) ^ FROM ("A".."Z")),
  zipCode NumericString (SIZE(5 | 9))
}

ListOfItems ::= SEQUENCE (SIZE (1..100)) OF Item

Item ::= SEQUENCE {
  itemCode        INTEGER (1..99999),
  color           VisibleString ("Black" | "Blue" | "Brown"),
  power           INTEGER (110 | 220)
}
END
"""