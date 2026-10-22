"""System tray icon — keeps the app alive in the hidden icons area
when the window is closed instead of quitting."""

import threading


def _load_icon_image():
    from PIL import Image, ImageDraw

    from core.paths import resource_path

    icon_path = resource_path("assets", "icon.ico")
    if icon_path.exists():
        try:
            return Image.open(icon_path)
        except Exception:
            pass

    # Fallback: draw a simple placeholder icon (no bundled asset required).
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, size - 4, size - 4), radius=14, fill=(103, 80, 164, 255))
    draw.ellipse((18, 18, size - 18, size - 18), fill=(255, 255, 255, 255))
    return img


class TrayIcon:
    """Thin wrapper around a pystray.Icon running on a background thread.

    pystray callbacks fire on that background thread, never on the Tk
    main thread — the provided callbacks are expected to be thread-safe
    (the caller should hop back via `Tk.after`).
    """

    def __init__(self, tooltip: str, on_restore, on_quit):
        self._tooltip = tooltip
        self._on_restore = on_restore
        self._on_quit = on_quit
        self._icon = None
        self._thread = None

    def is_visible(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def show(self, open_label: str, quit_label: str):
        if self.is_visible():
            return
        import pystray

        image = _load_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem(open_label, self._handle_restore, default=True),
            pystray.MenuItem(quit_label, self._handle_quit),
        )
        self._icon = pystray.Icon("game_manager", image, self._tooltip, menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def hide(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
        self._thread = None

    def _handle_restore(self, icon, item):
        self.hide()
        self._on_restore()

    def _handle_quit(self, icon, item):
        self.hide()
        self._on_quit()
