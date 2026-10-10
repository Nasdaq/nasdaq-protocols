.. _user-guide-fix:

FIX User Guide
===============

The `nasdaq_protocols.fix` module provides a client-side implementation of the FIX
protocol, including the session layer. Refer :ref:`api-reference-fix`. for more information
on the API.

This package **only** provides the core implementation of the FIX protocol (message
serialization, deserialization, validation and session handling). It **does not** define
any actual FIX messages -- those are application/dictionary specific and must be defined by
the user of this package (for example, by generating them from a FIX dictionary). The
session layer operates generically on the standard header/body tags and message *types*,
so the same session works for any conforming message set.

Follow the steps in :ref:`user-guide-create-new-project` to create a new python package for
the application specific messages.


Connecting to a FIX server
---------------------------

.. code-block:: python

    import asyncio
    from nasdaq_protocols import fix
    # `Fix44Session`/`Fix50Session` are provided by the library; the login message type
    # is defined by your application/dictionary.
    from nasdaq_protocols.fix.session import Fix44Session


    async def main():
        login_msg = ...  # build your application Logon message

        session = await fix.connect_async(
            ('hostname', 1234),
            login_msg,
            Fix44Session,
        )

        # ... use the session ...

        await session.close()


    if __name__ == '__main__':
        asyncio.run(main())


Session-level sequence recovery
-------------------------------

``FixSession`` always behaves as a compliant FIX client on the **receiver side**: it checks
for a sequence gap once, at login, and transparently performs the session-layer recovery
protocol before handing messages to your application. This is core functionality and cannot
be disabled.

.. code-block:: python

    session = await fix.connect_async(
        ('hostname', 1234),
        login_msg,
        lambda: Fix44Session(
            expected_seq_num=42,        # the next inbound MsgSeqNum you expect from the server
            client_heartbeat_interval=10,
            server_heartbeat_interval=10,
        ),
    )

``expected_seq_num`` defaults to ``None``: the session bootstraps itself from the
``MsgSeqNum`` of the ``Logon`` response, so whatever the server sends first is accepted as
the baseline. Pass an explicit value (e.g. derived from your persisted sequence store on a
reconnect) to detect a gap right from the login handshake.

A FIX session runs over a single TCP connection, which guarantees in-order, gap-free
delivery for the life of that connection -- a real gap can only arise from a disconnect and
reconnect. Because of this, gap detection happens **only once, during login**: the session
compares the ``MsgSeqNum`` the server reports on its ``Logon`` response against
``expected_seq_num``. If the server's sequence is higher, messages were missed on a prior
connection and recovery kicks in; once recovery completes, messages flow straight through to
your application with no further per-message sequence bookkeeping.

What the session does automatically:

- **No gap at login**: the ``Logon`` response's own ``MsgSeqNum`` matches (or bootstraps)
  ``expected_seq_num``; every subsequent message is checked against the expected sequence
  (a cheap O(1) comparison) and delivered to your ``on_msg_coro`` in order.
- **Gap detected at login**: the ``Logon`` response reports a ``MsgSeqNum`` ahead of
  ``expected_seq_num``. The session sends an open-ended
  ``ResendRequest(BeginSeqNo=expected_seq_num, EndSeqNo=0)``, asking the server to replay
  everything from the missing sequence onward. The optional ``on_gap`` hook is invoked with
  ``(expected_seq_num, received_seq)``.
- **No buffering**: the session never buffers out-of-order traffic. Any message that arrives
  *ahead* of ``expected_seq_num`` (for example, live traffic racing the in-flight
  ``ResendRequest``) is dropped silently before it is ever queued for your application --
  because the ``ResendRequest`` is open-ended, the server's replay naturally re-delivers
  that same message later (marked ``PossDupFlag=Y``), in the correct position, once the gap
  has been filled.
- **Gap fill / replay**: a ``SequenceReset`` with ``GapFillFlag=Y`` advances the expected
  sequence to ``NewSeqNo`` (the server may collapse a run of housekeeping messages, e.g.
  several ``Heartbeat``\ s, into a single ``GapFill``); a ``SequenceReset`` without the
  gap-fill flag forces the expected sequence to ``NewSeqNo``.
- **Duplicates**: a message *below* the expected sequence carrying ``PossDupFlag=Y`` is a
  replayed duplicate and is dropped silently.
- **Fatal sequence error**: a message *below* the expected sequence **without**
  ``PossDupFlag=Y`` is a fatal condition -- the session sends a ``Logout`` and closes.
- **TestRequest**: an inbound ``TestRequest`` is always answered with a ``Heartbeat``
  echoing the ``TestReqID`` -- the standard FIX flow.

This filtering happens at the point messages are received off the wire, before they are
ever handed to the dispatcher -- so your application only ever sees messages in strict
sequence order, and ``on_msg_coro``/``receive_msg()`` behave exactly as documented by the
base session, regardless of whether sequence recovery is in progress.

There is no cap on how long the server can take to complete the replay; if it never does,
the normal heartbeat-timeout logic closes the session as a safety net.

.. note::

    This is Phase 1 (receiver side). Responder-side replay -- replaying *our own* previously
    sent messages when the *server* sends *us* a ``ResendRequest`` -- requires a persistent
    outbound message store and is planned as future work.


Sending messages with an explicit sequence
-------------------------------------------

``send_msg`` auto-stamps the outbound ``MsgSeqNum`` from the session counter. Two keyword-only
parameters let you override that when producing recovery messages:

.. code-block:: python

    # Normal send: MsgSeqNum is taken from the session's outbound counter.
    session.send_msg(msg)

    # Send with an explicit sequence number; the auto counter is NOT advanced.
    session.send_msg(msg, seq_num=100)

    # Mark a message as a possible duplicate: sets PossDupFlag and OrigSendingTime.
    session.send_msg(msg, seq_num=100, poss_dup=True)
