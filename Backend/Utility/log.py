import asyncio
from typing import Any

# Bounded so that log entries emitted while no SSE client is connected
# (nobody draining the queue) don't accumulate in memory forever.
_MAX_QUEUED = 500
log_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_MAX_QUEUED)

_loop: asyncio.AbstractEventLoop | None = None


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Record the server's event loop, called once at startup.

    send_log() is invoked from FastAPI's sync (def, not async def) route
    handlers, which Starlette runs in a worker thread, not the event loop
    thread. call_soon_threadsafe is the only safe way to touch an
    asyncio.Queue from there.
    """
    global _loop
    _loop = loop


def _enqueue(message: str, level: str) -> None:
    if log_queue.full():
        try:
            log_queue.get_nowait()  # drop oldest to make room for the new entry
        except asyncio.QueueEmpty:
            pass
    log_queue.put_nowait({"message": message, "level": level})


def send_log(message: str, level: str = "info") -> None:
    """Fire-and-forget log emit. Safe to call from any thread."""
    if _loop is None:
        return
    _loop.call_soon_threadsafe(_enqueue, message, level)
