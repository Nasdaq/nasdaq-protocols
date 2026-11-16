(install-guide)=
# Installation

`nasdaq-protocols` requires **Python 3.10+**.

## Install from PyPI

```console
$ pip install nasdaq-protocols
```

## Optional performance extras

For improved async throughput, install with the `performance` extra. This pulls in
[uvloop](https://github.com/MagicStack/uvloop) (Linux/macOS only), which provides ~4-5x
faster event loop scheduling:

```console
$ pip install nasdaq-protocols[performance]
```

Activate it early in your application, before any asyncio work:

```python
from nasdaq_protocols.common import use_fast_loop
use_fast_loop()
```

If `uvloop` is not installed, `use_fast_loop()` is a no-op.

## Setting up a development environment

This project uses [uv](https://docs.astral.sh/uv/) for dependency management, building,
testing, linting and docs. Clone the repo and run:

```console
$ uv sync --group dev
```

See the {ref}`developer-guide` for the full contributor workflow.
