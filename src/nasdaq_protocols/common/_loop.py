"""Optional fast event loop integration."""


def use_fast_loop():
    """Install uvloop as the default event loop policy if available.

    Call this early in your application entry point before creating any
    asyncio event loops. If uvloop is not installed, this is a no-op.

    Install with: pip install nasdaq-protocols[performance]
    """
    try:
        import uvloop  # pylint: disable=import-outside-toplevel
        uvloop.install()
    except ImportError:
        pass
