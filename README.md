# 📡 Nasdaq Protocols Python Library

[![PyPI version](https://img.shields.io/pypi/v/nasdaq-protocols.svg)](https://pypi.org/project/nasdaq-protocols/)
[![Python versions](https://img.shields.io/pypi/pyversions/nasdaq-protocols.svg)](https://pypi.org/project/nasdaq-protocols/)
[![Build status](https://github.com/Nasdaq/nasdaq-protocols/actions/workflows/wf-push.yml/badge.svg)](https://github.com/Nasdaq/nasdaq-protocols/actions/workflows/wf-push.yml)
[![Documentation](https://img.shields.io/badge/docs-github--pages-blue)](https://nasdaq.github.io/nasdaq-protocols/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/nasdaq-protocols.svg)](https://pypi.org/project/nasdaq-protocols/)

`nasdaq-protocols` contains client-side implementations of the various publicly available
protocols used across the Nasdaq ecosystem.

This package provides only the **core** implementations -- message serialization,
deserialization, message validation and session handling. It does **not** ship any
concrete application messages exchanged between client and server: those are
application/protocol-specific and are defined by the user of this library by extending the
base message classes provided here.

📚 **Full documentation:** [nasdaq.github.io/nasdaq-protocols](https://nasdaq.github.io/nasdaq-protocols/)

---

## ✨ Supported protocols

| Protocol | Description | User guide | API reference |
|---|---|---|---|
| 🧦 **SOUP** (SoupBinTCP) | Sequenced message delivery transport underlying the app protocols below | [guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_soup.html) | [reference](https://nasdaq.github.io/nasdaq-protocols/api_reference_soup.html) |
| 🛒 **OUCH** | Order entry protocol | [guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_ouch.html) | [reference](https://nasdaq.github.io/nasdaq-protocols/api_reference_ouch.html) |
| 📈 **ITCH** | Market data feed protocol | [guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_itch.html) | [reference](https://nasdaq.github.io/nasdaq-protocols/api_reference_itch.html) |
| 💬 **SQF** | Quote feed protocol | [guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_sqf.html) | [reference](https://nasdaq.github.io/nasdaq-protocols/api_reference_sqf.html) |
| 🔁 **FIX** | FIX session layer (44/50), with session-level sequence gap detection/recovery | [guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_fix.html) | [reference](https://nasdaq.github.io/nasdaq-protocols/api_reference_fix.html) |

Application-specific messages for any of the protocols above are defined by generating a new
companion package with the bundled `nasdaq-protocols-create-new-project` CLI -- see the
[Create New Project guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_create_new_project.html).

## 🚀 Quickstart

```bash
pip install nasdaq-protocols
```

```python
import asyncio
from nasdaq_protocols import soup


async def main():
    session = await soup.connect_async(
        ('hostname', 1234),
        'username',   # max 6 characters
        'password',   # max 10 characters
        sequence=1,   # 0 = from HEAD, 1 = from start, n = from sequence n
    )
    message = await session.receive_msg()
    print(message)
    await session.close()


asyncio.run(main())
```

See the [User Guide](https://nasdaq.github.io/nasdaq-protocols/user_guide.html) for a
walkthrough of each protocol, and the
[Create New Project guide](https://nasdaq.github.io/nasdaq-protocols/user_guide_create_new_project.html)
for defining your own application messages.

## ⚡ Performance

For improved throughput, install the optional performance dependencies:

```bash
pip install nasdaq-protocols[performance]
```

This installs [uvloop](https://github.com/MagicStack/uvloop) (Linux/macOS only), which
provides ~4-5x faster event loop scheduling.

To activate it, call early in your application before any asyncio work:

```python
from nasdaq_protocols.common import use_fast_loop
use_fast_loop()
```

If uvloop is not installed, `use_fast_loop()` is a no-op.

## 🛠️ Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the development
workflow, and the
[Developer's Guide](https://nasdaq.github.io/nasdaq-protocols/developer_guide.html) for
more detail.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
