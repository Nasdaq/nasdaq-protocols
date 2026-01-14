.. _user-guide-itch:

ITCH User Guide
===============

The `nasdaq_protocols.itch` module provides an API to interact with ITCH servers.
Refer :ref:`api-reference-itch`. for more information on the API.

This package **only** provides the core implementation of the ITCH protocols, like message serialization
deserialization, session handling, etc. It **does not** define any actual ITCH messages. The actual ITCH
messages has to be defined by the user of this package. The first step is to create a new python package
which contains the messages definitions for all the protocols that the user wants to use.

This package provides a command line utility `nasdaq-protocols-create-new-project` to create a new python package
and all the necessary files.

Follow the steps in :ref:`user-guide-create-new-project` to create a new python package for application specific
messages.


.. note::

    This rest of the guide assumes that you have built a new python project using the steps mentioned in
    :ref:`user-guide-create-new-project`.


The generated project will contain a file `itch_<app_name>.py` which will contain the following
    - ITCH message definitions
    - ITCH Client Session for this application

Using the generated code, you can connect to a ITCH server and start receiving messages.


The `nasdaq_protocols.itch` module provides an API to interact with ITCH servers.
Refer :ref:`api-reference-itch`. for more information on the API.


Connecting to a ITCH Server
---------------------------
Use the example below to implement a program that will tail itch messages from the server.

.. code-block:: python

    #!/usr/bin/env python
    import asyncio
    # from the generated package we import the application we want to use
    from nasdaq_protocols_messages import itch_feed


    stopped = asyncio.Event()
    port = 1234  # give the proper itch server port


    async def itch_output(itch_message):
        """
        This function will be called whenever a new ITCH message is received
        """
        print('')
        print(f'received: {itch_message}')
        print('')


    async def itch_close():
        """
        This function will be called when the ITCH session is closed
        """
        stopped.set()
        print('')
        print('itch session closed, Bye Bye')
        print('')


    async def main():
        # Step1: connect
        itch_session = await itch_feed.connect_async(
            ('hostname', port),
            'itch username',  # itch username, max 6 characters
            'pwdchange', # itch password, max 10 characters
            '', # session id
            on_msg_coro=itch_output,  # function to call when a new message is received
            on_close_coro=itch_close, # function to call when the session is closed
            sequence=1  # 0 to listen from HEAD, 1 to listen from start, n to listen from n
        )

        print("wait for server to close the session")
        await stopped.wait()


    if __name__ == '__main__':
        asyncio.run(main())

*A simple itch tail program*

Slightly modified version where we do not use dispatchers instead explicitly call `receive_message()` method.

.. code-block:: python

    #!/usr/bin/env python
    import asyncio
    from nasdaq_protocols_messages import itch_feed


    port = 1234  # give the proper itch server port


    async def main():
        # Step1: connect
        itch_session = await itch_feed.connect_async(
            ('hostname', port),
            'itch username',  # itch username, max 6 characters
            'pwdchange', # itch password, max 10 characters
            '', # session id
            sequence=1  # 0 to listen from HEAD, 1 to listen from start, n to listen from n
        )

        # receive the first message from the server.
        itch_message = await itch_session.receive_message()
        print(itch_message)

        print("Closing the itch session...")
        await itch_session.close()


    if __name__ == '__main__':
        asyncio.run(main())
