User Guide
==========

SOUP
____

Connect to Soup session
-----------------------
Example of connecting to a Soup session and receiving messages.

.. code-block:: python

    import asyncio
    from nasdaq_protocols import Soup

    stopped = asyncio.Event()

    async def on_msg(msg):
        print(msg)

    async def on_close():
        stopped.set()
        print('closed')

    async def main():
        session = await soup.connect_async(
            ('host', port), 'user', 'password',
            sequence=1, on_msg_coro=on_msg, on_close_coro=on_close
        )
        await stopped.wait()

    if __name__ == '__main__':
        asyncio.run(main())

*A simple soup tail program*