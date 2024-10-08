.. _user-guide-soup:

SOUP User Guide
===============

SoupBinTCP 4.00 is a lightweight point-to-point protocol, built on top of TCP/IP
sockets that allow delivery of a set of sequenced and unsequenced messages from a
server to a client in real-time. SoupBinTCP guarantees that the client receives each
sequenced message generated by the server in the correct order, even across
underlying TCP/IP socket connection failures.

Refer to the `Official SOUP Documentation <https://www.nasdaq.com/docs/SoupBinTCP%204.0.pdf>`_ for more information
on how SOUP protocol works.

The `nasdaq_protocols.soup` module provides an API to interact with SOUP servers and clients.
Refer :ref:`api-reference-soup`. for more information on the API.


Connect to Soup Server
----------------------
Example of connecting to a Soup server and receiving messages.

.. code-block:: python

    #!/usr/bin/env python3
    import asyncio
    from nasdaq_protocols import soup


    stopped = asyncio.Event()


    async def on_msg(msg):
        print(msg)


    async def on_close():
        stopped.set()
        print('closed')


    async def main():
        port = 1234  # Give the actual port number
        session = await soup.connect_async(
            ('hostname or ip', port),
            'username', # Soup username, max 6 characters (as per spec)
            'password', # Soup password, max 10 characters (as per spec)
            sequence=1, # 0 to listen from HEAD, 1 to listen from start, n to listen from n
            on_msg_coro=on_msg, # callback for receiving messages
            on_close_coro=on_close # callback for indicating server closed the connection
        )

        # To send a message to the server
        # session.send_unseq_data(b'some bytes')

        await stopped.wait()


    if __name__ == '__main__':
        asyncio.run(main())

*A simple soup tail program*


A slightly modified version of the same example but not using dispatchers for `on_msg` and `on_close` callbacks.


.. code-block:: python

    #!/usr/bin/env python3
    import asyncio
    from nasdaq_protocols import soup


    async def main():
        port = 1234  # Give the actual port number
        session = await soup.connect_async(
            ('hostname or ip', port), 'username', 'password',
            sequence=1
        )
        print(await session.receive_msg())
        await session.close()

        # To send a message to the server
        # session.send_unseq_data(b'some bytes')


    if __name__ == '__main__':
        asyncio.run(main())

*A simple soup tail program without dispatchers*