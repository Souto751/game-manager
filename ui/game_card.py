"""Game card widget.

Each card is ONE plain tk.Label showing a single pre-rendered image (cover,
platform badge, menu chip, name and Play button all drawn with Pillow).
Clicks are routed by position. Earlier versions stacked ~12 CustomTkinter
widgets per card; with big libraries Windows sometimes failed to repaint some
of them (names drawn over the cover, missing Play buttons), and they were slow
to create. A single image per card can't come apart and builds much faster.
"""

import hashlib
import io
import os
import re
import threading
import time
import tkinter as tk
import urllib.request
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageTk

from ui import theme
from ui.dispatch import post
from ui.strings import t
from core.game_manager import Game
from core.paths import covers_dir

# Layout in logical pixels (multiplied by the Windows display scaling).
CARD_WIDTH = 180
CARD_RADIUS = 12
COVER_WIDTH = CARD_WIDTH             # full-bleed cover, edge to edge
COVER_HEIGHT = 240                   # 3:4, close to store box art with little crop
FADE_HEIGHT = 46                     # cover fades into the card color at the bottom
NAME_LINES = 2
NAME_TOP = COVER_HEIGHT + 6
NAME_LINE_HEIGHT = 19
NAME_HEIGHT = 40
NAME_X = 13
BUTTON_HEIGHT = 34
CARD_HEIGHT = COVER_HEIGHT + 6 + NAME_HEIGHT + 8 + BUTTON_HEIGHT + 12
CHIP_COLOR = (22, 20, 26)            # dark chips floating over covers (badge, menu)
SUPERSAMPLE = 2                      # draw at 2x and downscale: smooth corners and text

# Hit areas (x0, y0, x1, y1), logical pixels.
PLAY_BOX = (12, CARD_HEIGHT - 12 - BUTTON_HEIGHT, CARD_WIDTH - 12, CARD_HEIGHT - 12)
MENU_BOX = (CARD_WIDTH - 10 - 30, 10, CARD_WIDTH - 10, 30)
_MENU_HIT = (MENU_BOX[0] - 4, MENU_BOX[1] - 4, MENU_BOX[2] + 4, MENU_BOX[3] + 4)

# Network lookups/downloads (slow) and local rendering (fast) use separate
# pools, so a slow download never delays drawing the other cards.
_COVER_POOL = ThreadPoolExecutor(max_workers=6, thread_name_prefix="cover")
_RENDER_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="card")


def _cached_cover_path(url: str) -> Path:
    m = re.search(r"/apps/(\d+)/", url)
    key = f"steam_{m.group(1)}" if m else hashlib.md5(url.encode()).hexdigest()
    return covers_dir() / f"{key}.jpg"


# ── Colors (main thread) ──────────────────────────────────────────────────────

def _hex_rgb(color: str) -> tuple:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _mode_color(pair) -> tuple:
    return _hex_rgb(pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0])


def _widget_bg(widget) -> Optional[tuple]:
    """Actual background color behind the card (what its rounded corners show)."""
    try:
        # tk.Frame.cget reads the real Tk option (CustomTkinter widgets override cget).
        r, g, b = widget.winfo_rgb(tk.Frame.cget(widget, "bg"))
        return (r >> 8, g >> 8, b >> 8)
    except Exception:
        return None


def _palette_for(parent) -> dict:
    """Everything the renderer needs, resolved on the main thread (workers must
    not touch Tk/CustomTkinter)."""
    return {
        "page": _widget_bg(parent) or _mode_color(theme.BACKGROUND),
        "card": _mode_color(theme.CARD_BG),
        "card_hover": _mode_color(theme.CARD_HOVER),
        "accent": _mode_color(theme.PRIMARY),
        "text": _mode_color(theme.ON_SURFACE),
        "on_primary": _mode_color(theme.ON_PRIMARY),
    }


def _palette_key(p: dict) -> tuple:
    return tuple(sorted(p.items()))


def _mix(a: tuple, b: tuple, amount: float) -> tuple:
    return tuple(int(x + (y - x) * amount) for x, y in zip(a, b))


# ── Pillow rendering (worker threads) ─────────────────────────────────────────

_cache_lock = threading.Lock()
_static_cache: dict = {}
_content_cache: "OrderedDict[tuple, Image.Image]" = OrderedDict()
_CONTENT_CACHE_SIZE = 200


def _static(key, build):
    with _cache_lock:
        if key in _static_cache:
            return _static_cache[key]
    value = build()
    with _cache_lock:
        _static_cache.setdefault(key, value)
        return _static_cache[key]


_FONT_FILES = {
    "bold": ("segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "semibold": ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "regular": ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"),
}


def _font(weight: str, px: int):
    def build():
        for name in _FONT_FILES[weight]:
            try:
                return ImageFont.truetype(name, px)
            except OSError:
                continue
        try:
            return ImageFont.load_default(size=px)
        except TypeError:
            return ImageFont.load_default()
    return _static(("font", weight, px), build)


def _fit_cover(img: Image.Image, f: float) -> Image.Image:
    """Crop/scale to the cover box without distorting."""
    size = (round(COVER_WIDTH * f), round(COVER_HEIGHT * f))
    return ImageOps.fit(img.convert("RGB"), size, Image.LANCZOS, centering=(0.5, 0.3))


def _placeholder(initial: str, pal: dict, f: float) -> Image.Image:
    """Cover for games without art: soft gradient plus the game's initial."""
    w, h = round(COVER_WIDTH * f), round(COVER_HEIGHT * f)

    def build_gradient():
        column = Image.new("RGB", (1, h))
        for y in range(h):
            column.putpixel((0, y), _mix(pal["accent"], pal["card"], y / (h - 1)))
        return column.resize((w, h))

    img = _static(("gradient", _palette_key(pal), w, h), build_gradient).copy()
    ImageDraw.Draw(img).text((w / 2, h * 0.42), initial, font=_font("bold", round(64 * f)),
                             fill=(255, 255, 255), anchor="mm")
    return img


def _skeleton(pal: dict, f: float) -> Image.Image:
    """Neutral "loading" cover."""
    w, h = round(COVER_WIDTH * f), round(COVER_HEIGHT * f)
    base = tuple(min(255, c + 14) for c in pal["card"])
    band = tuple(min(255, c + 24) for c in pal["card"])
    img = Image.new("RGB", (w, h), base)
    draw = ImageDraw.Draw(img)
    r = 6 * f
    draw.rounded_rectangle((w * 0.18, h * 0.40, w * 0.82, h * 0.40 + 14 * f), radius=r, fill=band)
    draw.rounded_rectangle((w * 0.30, h * 0.40 + 24 * f, w * 0.70, h * 0.40 + 36 * f),
                           radius=r, fill=band)
    return img


def _wrap_name(text: str, font, max_width: float) -> list:
    """Word-wrap to NAME_LINES lines, ending with "…" if the name doesn't fit."""
    def fits(s: str) -> bool:
        return font.getlength(s) <= max_width

    def trim(s: str) -> str:
        while s and not fits(s + "…"):
            s = s[:-1]
        return s.rstrip() + "…"

    lines: list = []
    current = ""
    overflow = False
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if fits(candidate):
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == NAME_LINES:
            overflow = True
            break
    else:
        if current:
            lines.append(current)
    if len(lines) > NAME_LINES:
        overflow = True
    lines = [line if fits(line) else trim(line) for line in lines[:NAME_LINES]]
    if overflow and lines and not lines[-1].endswith("…"):
        lines[-1] = trim(lines[-1])
    return lines


def _card_mask(w: int, h: int, r: int) -> Image.Image:
    def build():
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
        return mask
    return _static(("card_mask", w, h, r), build)


def _fade_mask(w: int, h: int, fade: int) -> Image.Image:
    def build():
        alpha = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(alpha)
        for i in range(fade):
            y = h - fade + i
            draw.line([(0, y), (w, y)], fill=int(255 * (i / fade) ** 1.6))
        return alpha
    return _static(("fade", w, h, fade), build)


def _render_card(cover: Image.Image, info: dict, pal: dict, scale: float, hover: bool) -> Image.Image:
    """Draw the whole card at SUPERSAMPLE x scale and downscale to screen pixels."""
    f = scale * SUPERSAMPLE

    def S(v):
        return round(v * f)

    w, h = S(CARD_WIDTH), S(CARD_HEIGHT)
    card_color = pal["card_hover"] if hover else pal["card"]
    body = Image.new("RGB", (w, h), card_color)

    # Cover, fading into the card color at the bottom.
    if hover:
        cover = ImageEnhance.Brightness(cover).enhance(1.12)
    cw, ch = cover.size
    cover = Image.composite(Image.new("RGB", (cw, ch), card_color), cover,
                            _fade_mask(cw, ch, S(FADE_HEIGHT)))
    body.paste(cover, (0, 0))
    draw = ImageDraw.Draw(body)

    # Platform badge (top-left).
    if info["badge"]:
        bf = _font("bold", S(10))
        tw = bf.getlength(info["badge"])
        x0, y0 = S(10), S(10)
        draw.rectangle((x0, y0, x0 + tw + S(12), y0 + S(20)), fill=info["badge_bg"])
        draw.text((x0 + S(6), y0 + S(10)), info["badge"], font=bf,
                  fill=info["badge_fg"], anchor="lm")

    # Options chip (top-right): three dots.
    x0, y0, x1, y1 = (S(v) for v in MENU_BOX)
    draw.rectangle((x0, y0, x1, y1), fill=CHIP_COLOR)
    cy, rad = (y0 + y1) / 2, S(1.6)
    for dx in (-6, 0, 6):
        cx = (x0 + x1) / 2 + S(dx)
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(255, 255, 255))

    # Name, up to two lines.
    nf = _font("bold", S(13))
    lines = _wrap_name(info["name"], nf, S(CARD_WIDTH - 2 * NAME_X))
    for i, line in enumerate(lines):
        draw.text((S(NAME_X), S(NAME_TOP + 2 + i * NAME_LINE_HEIGHT)), line,
                  font=nf, fill=pal["text"], anchor="la")

    # Play button: pill with a triangle and the label, centered.
    x0, y0, x1, y1 = (S(v) for v in PLAY_BOX)
    btn = _mix(pal["accent"], (255, 255, 255), 0.14) if hover else pal["accent"]
    draw.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=btn)
    lf = _font("semibold", S(12))
    label = info["play"]
    tri_w, tri_h, gap = S(8), S(10), S(8)
    total = tri_w + gap + lf.getlength(label)
    left = (x0 + x1) / 2 - total / 2
    mid = (y0 + y1) / 2
    draw.polygon([(left, mid - tri_h / 2), (left, mid + tri_h / 2), (left + tri_w, mid)],
                 fill=pal["on_primary"])
    draw.text((left + tri_w + gap, mid), label, font=lf, fill=pal["on_primary"], anchor="lm")

    # Rounded card on the page background.
    out = Image.new("RGB", (w, h), pal["page"])
    out.paste(body, (0, 0), _card_mask(w, h, S(CARD_RADIUS)))
    return out.resize((round(CARD_WIDTH * scale), round(CARD_HEIGHT * scale)), Image.LANCZOS)


def _cover_content(key: tuple, load, f: float) -> Optional[Image.Image]:
    """Fitted cover image, memoised so filters and re-renders are instant."""
    cache_key = (key, f)
    with _cache_lock:
        if cache_key in _content_cache:
            _content_cache.move_to_end(cache_key)
            return _content_cache[cache_key]
    content = load()
    if content is None:
        return None
    with _cache_lock:
        _content_cache[cache_key] = content
        while len(_content_cache) > _CONTENT_CACHE_SIZE:
            _content_cache.popitem(last=False)
    return content


def _load_file(path: Path, f: float):
    def load():
        try:
            with Image.open(path) as img:
                return _fit_cover(img, f)
        except Exception:
            return None
    return load


def _hint_for(game: Game) -> Optional[tuple]:
    """Online lookup to use when a game has no cover (also for libraries saved by v1.0)."""
    if game.cover_fetch_hint:
        hint = tuple(game.cover_fetch_hint)
        if hint[0] == "gog" and len(hint) < 3:
            hint = ("gog", hint[1] if len(hint) > 1 else "", game.name)  # v1.0 hints had no name
        return hint
    if game.platform == "epic":
        return ("epic", game.name)
    if game.platform == "ea":
        return ("ea", game.name, game.install_path)
    if game.platform in ("gog", "xbox", "custom") and game.name:
        return ("search", game.name)  # Steam store fallback by name
    return None


# Shared first-frame image (main thread): an empty skeleton card, so a new card
# has its final size and a placeholder before its own render arrives.
_blank_cards: dict = {}


def _blank_card(master, pal: dict, scale: float):
    key = (_palette_key(pal), scale)
    image = _blank_cards.get(key)
    if image is None:
        f = scale * SUPERSAMPLE
        sk = _static(("skeleton", _palette_key(pal), f), lambda: _skeleton(pal, f))
        info = {"name": "", "badge": "", "play": ""}
        image = ImageTk.PhotoImage(_render_card(sk, info, pal, scale, hover=False),
                                   master=master.winfo_toplevel())
        _blank_cards[key] = image
    return image


def _inside(box: tuple, x: float, y: float) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


class GameCard(tk.Label):
    # Stages of what the card shows; a late result never replaces a newer one.
    _STAGE_SKELETON, _STAGE_FINAL = 1, 2

    def __init__(self, parent, game: Game,
                 on_launch: Callable[[Game], None],
                 on_delete: Callable[[Game], None],
                 on_cover_resolved: Optional[Callable[[Game, str], None]] = None,
                 **kwargs):
        self._scale = self._read_scale(parent)
        self._pal = _palette_for(parent)
        super().__init__(parent, bd=0, padx=0, pady=0, highlightthickness=0,
                         bg=self._rgb_hex(self._pal["page"]),
                         image=_blank_card(parent, self._pal, self._scale), **kwargs)
        self.game = game
        self.on_launch = on_launch
        self.on_delete = on_delete
        self.on_cover_resolved = on_cover_resolved
        self._images: tuple = ()          # (normal, hover) PhotoImages
        self._stage = 0
        self._hover = False
        self._last_launch = 0.0
        self._alive = True
        self._info = {
            "name": game.name or "?",
            "badge": (game.platform or "").upper(),
            "badge_bg": _hex_rgb(theme.PLATFORM_COLORS.get(game.platform, "#16141A")),
            "badge_fg": _hex_rgb(theme.PLATFORM_TEXT.get(game.platform, "#CAC4D0")),
            "play": t("play"),
        }

        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label=t("play"), command=self._launch)
        self._menu.add_command(label=t("open_location"), command=self._open_location)
        self._menu.add_separator()
        self._menu.add_command(label=t("remove_from_library"), command=self._delete)

        self._bind_events()
        _RENDER_POOL.submit(self._skeleton_task)
        _COVER_POOL.submit(self._resolve_task)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _read_scale(widget) -> float:
        try:
            return float(ctk.ScalingTracker.get_widget_scaling(widget))
        except Exception:
            return 1.0

    @staticmethod
    def _rgb_hex(rgb: tuple) -> str:
        return "#%02x%02x%02x" % rgb

    def grid(self, **kwargs):
        # tk.Label doesn't scale paddings like CustomTkinter widgets do.
        for key in ("padx", "pady"):
            if key in kwargs:
                v = kwargs[key]
                kwargs[key] = (tuple(round(x * self._scale) for x in v)
                               if isinstance(v, tuple) else round(v * self._scale))
        return super().grid(**kwargs)

    def destroy(self):
        self._alive = False
        super().destroy()

    # ── Rendering (worker threads) ────────────────────────────────────────────

    @property
    def _f(self) -> float:
        return self._scale * SUPERSAMPLE

    def _render_and_post(self, cover: Image.Image, stage: int):
        if not self._alive:
            return
        try:
            normal = _render_card(cover, self._info, self._pal, self._scale, hover=False)
            hover = _render_card(cover, self._info, self._pal, self._scale, hover=True)
        except Exception:
            return
        post(self._show, stage, normal, hover)

    def _skeleton_task(self):
        sk = _static(("skeleton", _palette_key(self._pal), self._f),
                     lambda: _skeleton(self._pal, self._f))
        self._render_and_post(sk, self._STAGE_SKELETON)

    def _post_cover(self, key: tuple, load) -> bool:
        try:
            content = _cover_content(key, load, self._f)
        except Exception:
            content = None
        if content is None:
            return False
        self._render_and_post(content, self._STAGE_FINAL)
        return True

    def _post_placeholder(self):
        initial = (self.game.name or "?")[:1].upper()
        self._post_cover(("placeholder", initial, _palette_key(self._pal)),
                         lambda: _placeholder(initial, self._pal, self._f))

    def _post_file(self, key: tuple, path: Path):
        if not self._post_cover(key, _load_file(path, self._f)):
            self._post_placeholder()  # unreadable image file: fall back to the initial

    def _resolve_task(self):
        if not self._alive:
            return
        cover = self.game.cover_image
        if cover and cover.startswith(("http://", "https://")):
            cached = _cached_cover_path(cover)
            if cached.exists():
                self._post_file(("file", str(cached)), cached)
            else:
                self._download_task(cover, cached, None)
            return
        if cover and Path(cover).exists():
            self._post_file(("file", cover), Path(cover))
            return
        hint = _hint_for(self.game)
        if hint:
            self._hint_task(hint)
        else:
            self._post_placeholder()

    def _hint_task(self, hint: tuple):
        from core.cover_fetcher import fetch_cover_for_hint
        try:
            found = fetch_cover_for_hint(hint)
        except Exception:
            found = None
        if not found:
            self._post_placeholder()
            return
        if not found.startswith("http"):
            path = Path(found)
            if path.exists():
                self._remember(found)
                self._post_file(("file", found), path)
            else:
                self._post_placeholder()
            return
        cached = _cached_cover_path(found)
        if cached.exists():
            self._remember(found)
            self._post_file(("file", str(cached)), cached)
        else:
            self._download_task(found, cached, found)

    def _download_task(self, url: str, cache_path: Path, remember: Optional[str]):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GameManager/1.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            with Image.open(io.BytesIO(data)) as img:
                fitted = _fit_cover(img, self._f)
            cache_path.write_bytes(data)
        except Exception:
            self._post_placeholder()  # no art available: show the initial
            return
        if remember:
            self._remember(remember)
        self._post_cover(("file", str(cache_path)), lambda: fitted)

    def _remember(self, cover: str):
        if self.on_cover_resolved:
            try:
                self.on_cover_resolved(self.game, cover)
            except Exception:
                pass

    # ── Main thread ───────────────────────────────────────────────────────────

    def _show(self, stage: int, normal: Image.Image, hover: Image.Image):
        if not self._alive or stage < self._stage:
            return
        try:
            if not self.winfo_exists():
                return
            self._stage = stage
            self._images = (ImageTk.PhotoImage(normal, master=self),
                            ImageTk.PhotoImage(hover, master=self))
            self.configure(image=self._images[1 if self._hover else 0])
        except tk.TclError:
            pass

    def _bind_events(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Double-Button-1>", self._on_double)
        self.bind("<Button-3>", self._open_menu)  # right-click

    def _logical(self, event) -> tuple:
        return event.x / self._scale, event.y / self._scale

    def _on_click(self, event):
        x, y = self._logical(event)
        if _inside(PLAY_BOX, x, y):
            self._launch()
        elif _inside(_MENU_HIT, x, y):
            self._open_menu_from_button()

    def _on_double(self, event):
        x, y = self._logical(event)
        if not _inside(PLAY_BOX, x, y) and not _inside(_MENU_HIT, x, y):
            self._launch()

    def _on_motion(self, event):
        x, y = self._logical(event)
        hot = _inside(PLAY_BOX, x, y) or _inside(_MENU_HIT, x, y)
        cursor = "hand2" if hot else ""
        if str(self.cget("cursor")) != cursor:
            self.configure(cursor=cursor)

    def _on_enter(self, _event=None):
        self._hover = True
        if len(self._images) == 2:
            self.configure(image=self._images[1])

    def _on_leave(self, _event=None):
        self._hover = False
        if len(self._images) == 2:
            self.configure(image=self._images[0])

    def _open_menu(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _open_menu_from_button(self):
        x = self.winfo_rootx() + round(MENU_BOX[0] * self._scale)
        y = self.winfo_rooty() + round(MENU_BOX[3] * self._scale) + 2
        try:
            self._menu.tk_popup(x, y)
        finally:
            self._menu.grab_release()

    def _open_location(self):
        from tkinter import messagebox
        candidates = [self.game.install_path,
                      os.path.dirname(self.game.executable) if self.game.executable else ""]
        for folder in candidates:
            if folder and os.path.isdir(folder):
                os.startfile(folder)
                return
        messagebox.showinfo(self.game.name, t("location_not_found"))

    def _launch(self):
        # Guard against double launches (e.g. a fast double click on Play).
        now = time.monotonic()
        if now - self._last_launch < 1.5:
            return
        self._last_launch = now
        self.on_launch(self.game)

    def _delete(self):
        self.on_delete(self.game)
