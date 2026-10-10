(api-reference-fix)=
# FIX API Reference

## Fix

```{eval-rst}
.. automodule:: nasdaq_protocols.fix
```

### Fix Session

```{eval-rst}
.. autoclass:: nasdaq_protocols.fix.session.FixSessionId
    :show-inheritance: True
```

```{eval-rst}
.. autoclass:: nasdaq_protocols.fix.session.FixSession
    :show-inheritance: True
    :undoc-members: ['send_heartbeat']
    :members: login, send_msg
```

The following keyword-only constructor parameters configure the session-layer sequence
recovery (see {ref}`user-guide-fix` for the behaviour):

- `expected_seq_num` (int or `None`, default `None`) -- the next inbound `MsgSeqNum`
  expected from the counterparty. When `None`, the session bootstraps itself from the
  `MsgSeqNum` of the first inbound message (normally the `Logon` response).
- `on_gap` (coroutine `(expected, received) -> None` or `None`) -- optional hook
  invoked when an inbound gap is detected.

`send_msg` accepts two keyword-only parameters: `seq_num` (send with an explicit
`MsgSeqNum` without advancing the auto counter) and `poss_dup` (set `PossDupFlag` and
`OrigSendingTime`).

```{eval-rst}
.. autoclass:: nasdaq_protocols.fix.session.Fix44Session
    :show-inheritance: True
    :undoc-members: ['begin_string']
```

```{eval-rst}
.. autoclass:: nasdaq_protocols.fix.session.Fix50Session
    :show-inheritance: True
    :undoc-members: ['begin_string']
```

### Fix Messages

```{eval-rst}
.. automodule:: nasdaq_protocols.fix.core
```
