# Welcome to nasdaq-protocols's documentation!

nasdaq-protocols contains client side implementations of the various
publicly available protocols used by Nasdaq ecosystem.

This package contains only the core implementations of the protocols like message
serialization, deserialization, message validation and session handling. It does not
contain any actual messages that are exchanged between the client and the server.

The actual messages are application specific and hence has to be defined by the
user of this library. The user has to define the messages as per the protocol specification
by extending the base message class defined in the package.

Refer to the {ref}`user-guide`. for more information on how to define the messages and use this package.

```{toctree}
:maxdepth: 1
:caption: Contents:

user_guide
api_reference
developer_guide
LICENSE
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
