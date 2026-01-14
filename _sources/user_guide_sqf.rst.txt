.. _user-guide-sqf:

SQF User Guide
===============

The `nasdaq_protocols.sqf` module provides an API to interact with SQF servers.
Refer :ref:`api-reference-sqf`. for more information on the API.

This package **only** provides the core implementation of the SQF protocols, like message serialization
deserialization, session handling, etc. It **does not** define any actual SQF messages. The actual SQF
messages has to be defined by the user of this package. The first step is to create a new python package
which contains the messages definitions for all the protocols that the user wants to use.

This package provides a command line utility `nasdaq-protocols-create-new-project` to create a new python package
and all the necessary files.

Follow the steps in :ref:`user-guide-create-new-project` to create a new python package for application specific
messages.


.. note::

    This rest of the guide assumes that you have built a new python project using the steps mentioned in
    :ref:`user-guide-create-new-project`.


The generated project will contain a file `sqf_<app_name>.py` which will contain the following
    - SQF message definitions
    - SQF Client Session for this application

Using the generated code, you can connect to a SQF server and start sending/receiving messages.


The `nasdaq_protocols.sqf` module provides an API to interact with SQF servers.
Refer :ref:`api-reference-sqf`. for more information on the API.


Sending Message to a SQF Server
--------------------------------

Sample Message Definition
^^^^^^^^^^^^^^^^^^^^^^^^^
For our test sqf app, lets define our sqf messages in the file `<app_name>.xml` as follows,

.. code-block:: XML

    <root>
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
            <message id="QuoteAccepted" message-id="2" direction="outgoing">
                <fields>
                    <field name="quoteId" type="uint_8"/>
                </fields>
            </message>
        </messages-root>
    </root>


Sending and Receiving SQF messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the above message definition, we can now send the SQF message as follows.

.. code-block:: python

    #!/usr/bin/env python
    import asyncio
    # from the generated package we import the application we want to use
    from nasdaq_protocols_messages import sqf_oe


    port = 1234  # give the proper SQF server port


    async def main():
        # Step1: connect
        sqf_session = await sqf_oe.connect_async(
            ('hostname', port),
            'sqf username',  # SQF username, max 6 characters
            'pwdchange', # SQF password, max 10 characters
            '', # session id
            sequence=0  # 0 to listen from HEAD, 1 to listen from start, n to listen from n
        )

        # Step2: Prepare a message
        quotes = []
        for i in range(1, 2):
            quote = sqf_oe.Quote()
            quote.instrumentId = i
            quote.bidPrice = i * 100
            quote.askPrice = i * 1000
            quote.bidQuantity = i * 10
            quote.askQuantity = i * 100
            quotes.append(quote)

        msg = sqf_oe.QuoteMessage()
        msg.timestamp = key
        msg.someInfo = 'a' * 32
        msg.quotes = quotes
        return msg

        # Step3: Send the message to the server.
        sqf_session.send_message(msg)

        # Step4: receive the first message from the server.
        output = await sqf_session.receive_message()
        if isinstance(output, sqf_oe.QuoteAccepted):
            print("Quote accepted")

        # Step5: Close the session
        print("Closing the sqf session...")
        await sqf_session.close()


    if __name__ == '__main__':
        asyncio.run(main())

*A simple SQF send and receive program*
