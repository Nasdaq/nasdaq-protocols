.. _api-reference-fix:
FIX API Reference
=================

Fix
----
.. automodule:: nasdaq_protocols.fix


Fix Session
^^^^^^^^^^^
.. autoclass:: nasdaq_protocols.fix.session.FixSessionId
    :show-inheritance: True

.. autoclass:: nasdaq_protocols.fix.session.FixSession
    :show-inheritance: True
    :undoc-members: ['send_heartbeat']

.. autoclass:: nasdaq_protocols.fix.session.Fix44Session
    :show-inheritance: True
    :undoc-members: ['begin_string']

.. autoclass:: nasdaq_protocols.fix.session.Fix50Session
    :show-inheritance: True
    :undoc-members: ['begin_string']


Fix Messages
^^^^^^^^^^^^
.. automodule:: nasdaq_protocols.fix.core