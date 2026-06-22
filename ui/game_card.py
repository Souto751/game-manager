"""Game card widget."""

import io
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image

from ui import theme
from core.game_manager import Game

CARD_WIDTH = 180
CARD_HEIGHT = 280
COVER_WIDTH = 180
COVER_HEIGHT = 200


def _cover_cache_dir() -> Path:
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent.parent
    d = base / "data" / "covers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cached_cover_path(url: str) -> Path:
    import re, hashlib
    m = re.search(r"/apps/(\d+)/", url)
    key = m.group(1) if m else hashlib.md5(url.encode()).hexdigest()
    return _cover_cache_dir() / f"{key}.jpg"


class GameCard(ctk.CTkFrame):
    def __init__(self, parent, game: Game,
                 on_launch: Callable[[Game], None],
                 on_delete: Callable[[Game], None], **kwargs):
        super().__init__(parent, width=CARD_WIDTH, height=CARD_HEIGHT,
                         corner_radius=12, fg_color=theme.CARD_BG, **kwargs)
        self.game = game
        self.on_launch = on_launch
        self.on_delete = on_delete
        self.pack_propagate(False)
        self._build()
        self._bind_events()

    def _build(self):
        self._cover_label = ctk.CTkLabel(
            self, text="", width=COVER_WIDTH, height=COVER_HEIGHT,
            corner_radius=8, fg_color=theme.SURFACE_VARIANT)
        self._cover_label.pack()
        self._load_cover()

        badge_bg = theme.PLATFORM_COLORS.get(self.game.platform, theme.SURFACE_VARIANT)
        badge_fg = theme.PLATFORM_TEXT.get(self.game.platform, theme.ON_SURFACE_VARIANT)
        self._badge = ctk.CTkLabel(
            self, text=self.game.platform.upper(), font=theme.FONT_CAPTION,
            fg_color=badge_bg, text_color=badge_fg, corner_radius=4, padx=6, pady=2)
        self._badge.pack(anchor="w", padx=8, pady=(6, 2))

        self._name_label = ctk.CTkLabel(
            self, text=self.game.name, font=theme.FONT_BODY_BOLD,
            text_color=theme.ON_SURFACE, wraplength=CARD_WIDTH - 16,
            justify="left", anchor="w")
        self._name_label.pack(anchor="w", padx=8, pady=(0, 6))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._launch_btn = ctk.CTkButton(
            btn_frame, text="Jugar", font=theme.FONT_LABEL,
            height=28, corner_radius=20,
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_DARK,
            text_color=theme.ON_PRIMARY, command=self._launch)
        self._launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._delete_btn = ctk.CTkButton(
            btn_frame, text="X", font=theme.FONT_LABEL,
            width=28, height=28, corner_radius=20,
            fg_color=theme.SURFACE_CONTAINER_HIGH, hover_color=theme.ERROR,
            text_color=theme.ON_SURFACE_VARIANT, command=self._delete)
        self._delete_btn.pack(side="right")

    # ── Cover loading ─────────────────────────────────────────────────────────

    def _load_cover(self):
        cover = self.game.cover_image

        if cover:
            if cover.startswith("http://") or cover.startswith("https://"):
                cached = _cached_cover_path(cover)
                if cached.exists():
                    self._load_from_path(cached)
                else:
                    threading.Thread(target=self._fetch_url, args=(cover, cached), daemon=True).start()
                return
            elif Path(cover).exists():
                self._load_from_path(Path(cover))
                return

        # No cover or not found — try cover_fetch_hint
        hint = self.game.cover_fetch_hint
        if hint:
            threading.Thread(target=self._fetch_from_hint, args=(hint,), daemon=True).start()
        else:
            self._apply_cover(None)

    def _fetch_from_hint(self, hint: tuple):
        from core.cover_fetcher import fetch_epic_cover, fetch_ea_cover
        try:
            url_or_path = None
            if hint[0] == "epic":
                name = hint[1]
                url_or_path = fetch_epic_cover(name)
            elif hint[0] == "ea":
                name       = hint[1] if len(hint) > 1 else ""
                install    = hint[2] if len(hint) > 2 else ""
                content_id = hint[3] if len(hint) > 3 else ""
                url_or_path = fetch_ea_cover(name, content_id, install)

            if not url_or_path:
                return

            # Local file path
            if not url_or_path.startswith("http"):
                p = Path(url_or_path)
                if p.exists():
                    try:
                        self.after(0, lambda pp=p: self._load_from_path(pp))
                    except Exception:
                        pass
                return

            # Remote URL — check cache first
            cached = _cached_cover_path(url_or_path)
            if cached.exists():
                try:
                    self.after(0, lambda p=cached: self._load_from_path(p))
                except Exception:
                    pass
            else:
                self._fetch_url(url_or_path, cached)
        except Exception:
            pass

    def _fetch_url(self, url: str, cache_path: Path):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GameManager/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            cache_path.write_bytes(data)
            img = Image.open(io.BytesIO(data)).resize((COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS)
            image = ctk.CTkImage(img, size=(COVER_WIDTH, COVER_HEIGHT))
            try:
                self.after(0, lambda: self._apply_cover(image))
            except Exception:
                pass
        except Exception:
            pass

    def _load_from_path(self, path: Path):
        try:
            img = Image.open(path).resize((COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS)
            self._apply_cover(ctk.CTkImage(img, size=(COVER_WIDTH, COVER_HEIGHT)))
        except Exception:
            self._apply_cover(None)

    def _apply_cover(self, image):
        if image is None:
            self._cover_label.configure(
                text=self.game.name[0].upper() if self.game.name else "?",
                font=("Segoe UI", 48, "bold"), text_color=theme.PRIMARY_LIGHT)
        else:
            self._cover_label.configure(image=image, text="")
            self._cover_label._image = image

    # ── Events ────────────────────────────────────────────────────────────────

    def _bind_events(self):
        # Hover
        for w in [self, self._cover_label, self._name_label, self._badge]:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
        # Double-click to launch on all interactive surfaces
        for w in [self, self._cover_label, self._name_label]:
            w.bind("<Double-Button-1>", lambda e: self._launch())

    def _on_enter(self, _event=None):
        self.configure(fg_color=theme.CARD_HOVER)

    def _on_leave(self, _event=None):
        self.configure(fg_color=theme.CARD_BG)

    def _launch(self):
        self.on_launch(self.game)

    def _delete(self):
        self.on_delete(self.game)
