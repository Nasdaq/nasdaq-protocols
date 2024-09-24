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