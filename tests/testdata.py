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
        <message id="OuchEnterOrder" message-id="79" direction="incoming">
            <fields>
                <field name="orderToken" type="int_8_be"/>
                <field name="orderBookId" type="int_4_be"/>
                <field name="side" type="char_iso-8859-1"/>
                <field name="quantity" type="int_8_be"/>
                <field name="price" type="int_8_be"/>
                <field name="timeInForce" type="byte"/>
                <field name="openClose" type="byte"/>
                <field name="clientAccount" type="str_iso-8859-1_n" length="16"/>
                <field name="customerInfo" type="str_iso-8859-1_n" length="15"/>
                <field name="exchangeInfo" type="str_iso-8859-1_n" length="32"/>
                <field name="displayQuantity" type="int_8_be"/>
                <field name="orderType" type="byte"/>
                <field name="timeInForceData" type="int_2_be"/>
                <field name="orderCapacity" type="byte"/>
                <field name="selfMatchPreventionKey" type="int_4_be"/>
                <field name="attributes" type="int_2_be"/>
            </fields>
        </message>
    </messages-root>
</root>
"""