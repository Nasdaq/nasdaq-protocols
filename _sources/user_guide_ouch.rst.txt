.. _user-guide-ouch:

OUCH User Guide
===============

The `nasdaq_protocols.ouch` module provides an API to interact with OUCH servers.
Refer :ref:`api-reference-ouch`. for more information on the API.

This package **only** provides the core implementation of the OUCH protocols, like message serialization
deserialization, session handling, etc. It **does not** define any actual OUCH messages. The actual OUCH
messages has to be defined by the user of this package. The first step is to create a new python package
which contains the messages definitions for all the protocols that the user wants to use.

This package provides a command line utility `nasdaq-protocols-create-new-project` to create a new python package
and all the necessary files.

Follow the steps in :ref:`user-guide-create-new-project` to create a new python package for application specific
messages.


.. note::

    This rest of the guide assumes that you have built a new python project using the steps mentioned in
    :ref:`user-guide-create-new-project`.


The generated project will contain a file `ouch_<app_name>.py` which will contain the following
    - OUCH message definitions
    - OUCH Client Session for this application

Using the generated code, you can connect to a OUCH server and start sending/receiving messages.


The `nasdaq_protocols.ouch` module provides an API to interact with OUCH servers.
Refer :ref:`api-reference-ouch`. for more information on the API.


Sending Message to a OUCH Server
--------------------------------

Sample Message Definition
^^^^^^^^^^^^^^^^^^^^^^^^^
For our test ouch app, lets define our OUCH messages in the file `<app_name>.xml` as follows,

.. code-block:: XML

    <root>
        <messages-root>
            <message id="EnterOrder" message-id="65" direction="incoming">
                <fields>
                    <field name="orderBookId" type="int_4_be"/>
                    <field name="side" type="char_iso-8859-1"/>
                    <field name="quantity" type="int_8_be"/>
                    <field name="price" type="int_8_be"/>
                </fields>
            </message>
            <message id="Accepted" message-id="75" direction="outgoing">
                <fields>
                    <field name="orderId" type="int_8_be"/>
                </fields>
            </message>
            <message id="Rejected" message-id="85" direction="outgoing">
                <fields>
                    <field name="reason" type="int_2_be"/>
                </fields>
            </message>
        </messages-root>
    </root>


Sending and Receiving OUCH messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the above message definition, we can now send the ouch message as follows.

.. code-block:: python

    #!/usr/bin/env python
    import asyncio
    # from the generated package we import the application we want to use
    from nasdaq_protocols_messages import ouch_oe


    port = 1234  # give the proper ouch server port


    async def main():
        # Step1: connect
        ouch_session = await ouch_oe.connect_async(
            ('hostname', port),
            'ouch username',  # ouch username, max 6 characters
            'pwdchange', # ouch password, max 10 characters
            '', # session id
            sequence=0  # 0 to listen from HEAD, 1 to listen from start, n to listen from n
        )

        # Step2: Prepare a message
        enter_order = ouch_oe.EnterOrder()  # This is the message we defined in the xml file
        enter_order.orderBookId = 1
        enter_order.side = 'B'
        enter_order.quantity = 100
        enter_order.price = 20

        # Step3: Send the message to the server.
        ouch_session.send_message(enter_order)

        # Step4: receive the first message from the server.
        output = await ouch_session.receive_message()
        if isinstance(output, ouch_oe.Accepted):
            print("Order accepted")
        elif isinstance(output, ouch_oe.Rejected):
            print("Order rejected")

        # Step5: Close the session
        print("Closing the ouch session...")
        await ouch_session.close()


    if __name__ == '__main__':
        asyncio.run(main())

*A simple ouch send and receive program*
