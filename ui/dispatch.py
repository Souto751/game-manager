"""Run UI updates on the Tk main thread.

Tkinter is not thread-safe: background threads (cover downloads, store
imports, update checks) must never touch widgets directly. They call
`post(fn, *args)` and the main loop runs `fn` a moment later.
"""

import queue

_queue: "queue.Queue[tuple]" = queue.Queue()
_root = None
_INTERVAL_MS = 40


def install(root) -> None:
    """Start pumping the queue from the given Tk root (call once)."""
    global _root
    _root = root
    root.after(_INTERVAL_MS, _pump)


def post(fn, *args) -> None:
    """Schedule fn(*args) on the Tk main thread. Safe from any thread."""
    _queue.put((fn, args))


def _pump() -> None:
    try:
        while True:
            fn, args = _queue.get_nowait()
            try:
                fn(*args)
            except Exception:
                pass  # A widget may have been destroyed meanwhile; skip it.
    except queue.Empty:
        pass
    if _root is not None:
        try:
            _root.after(_INTERVAL_MS, _pump)
        except Exception:
            pass  # Root destroyed: the app is closing.
