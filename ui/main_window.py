"""Main application window."""

import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox
import threading

import customtkinter as ctk

from ui import theme
from ui.game_card import GameCard, CARD_WIDTH
from core.game_manager import Game, GameManager
from core.config_manager import ConfigManager
from core.folder_scanner import scan_folder
from core.updater import check_for_updates_async

_CARD_CELL = CARD_WIDTH + 16   # card width + padx 8 each side


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._cfg = ConfigManager()
        self.game_manager = GameManager()
        self._current_filter = "all"
        self._search_query = ""
        self._all_cards = []
        self._visible_cards = []
        self._last_columns = 0
        self._resize_job = None
        self._search_job = None

        self._configure_window()
        self._build_ui()
        self._highlight_filter("all")
        self._set_filter("all")
        self.bind("<Configure>", self._on_resize_debounced)
        # Force a relayout once the window is fully rendered and winfo_width is real.
        self.after(200, self._relayout_force)
        # Check for updates in background (waits 4 s before hitting network).
        check_for_updates_async(on_update_available=self._on_update_found)

    # ── Window setup ──────────────────────────────────────────────────────────

    def _configure_window(self):
        ctk.set_appearance_mode(self._cfg.get("theme") or "dark")
        ctk.set_default_color_theme("blue")
        self.title("Game Manager")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=theme.BACKGROUND)
        try:
            self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=theme.SURFACE)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(20, weight=1)

        ctk.CTkLabel(sidebar, text="Game Manager",
                     font=theme.FONT_TITLE, text_color=theme.PRIMARY_LIGHT,
                     anchor="w").grid(row=0, column=0, padx=20, pady=(24, 8), sticky="ew")

        # ── BIBLIOTECA ────────────────────────────────────────────────────────
        ctk.CTkLabel(sidebar, text="BIBLIOTECA", font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=1, column=0, padx=20, pady=(16, 4), sticky="ew")

        self._filter_buttons = {}
        filters = [
            ("all",    "Todos los juegos"),
            ("steam",  "Steam"),
            ("epic",   "Epic Games"),
            ("ea",     "EA App"),
            ("gog",    "GOG"),
            ("custom", "Personalizados"),
        ]
        for i, (key, label) in enumerate(filters, start=2):
            btn = ctk.CTkButton(
                sidebar, text=label, font=theme.FONT_BODY, anchor="w",
                corner_radius=8, height=38,
                fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                text_color=theme.ON_SURFACE_VARIANT,
                command=lambda k=key: self._set_filter(k))
            btn.grid(row=i, column=0, padx=12, pady=2, sticky="ew")
            self._filter_buttons[key] = btn

        # ── AGREGAR JUEGOS ────────────────────────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.OUTLINE_VARIANT).grid(
            row=9, column=0, padx=16, pady=12, sticky="ew")
        ctk.CTkLabel(sidebar, text="AGREGAR JUEGOS", font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=10, column=0, padx=20, pady=(0, 4), sticky="ew")

        ctk.CTkButton(sidebar, text="Escanear carpeta", font=theme.FONT_BODY,
                      anchor="w", corner_radius=8, height=38,
                      fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                      text_color=theme.ON_SURFACE_VARIANT,
                      command=self._scan_folder).grid(
                      row=11, column=0, padx=12, pady=2, sticky="ew")

        # ── CUENTAS ───────────────────────────────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.OUTLINE_VARIANT).grid(
            row=13, column=0, padx=16, pady=12, sticky="ew")
        ctk.CTkLabel(sidebar, text="CUENTAS", font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=14, column=0, padx=20, pady=(0, 4), sticky="ew")

        ctk.CTkButton(sidebar, text="Vincular cuentas", font=theme.FONT_BODY,
                      anchor="w", corner_radius=8, height=38,
                      fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                      text_color=theme.ON_SURFACE_VARIANT,
                      command=self._open_accounts).grid(
                      row=15, column=0, padx=12, pady=2, sticky="ew")

        # ── CONFIGURACION (fixed to bottom) ───────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.OUTLINE_VARIANT).grid(
            row=21, column=0, padx=16, pady=(12, 4), sticky="ew")

        ctk.CTkButton(sidebar, text="Configuracion", font=theme.FONT_BODY,
                      anchor="w", corner_radius=8, height=38,
                      fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                      text_color=theme.ON_SURFACE_VARIANT,
                      command=self._open_settings).grid(
                      row=22, column=0, padx=12, pady=(0, 8), sticky="ew")

        self._count_label = ctk.CTkLabel(
            sidebar, text="", font=theme.FONT_CAPTION,
            text_color=theme.OUTLINE, anchor="w")
        self._count_label.grid(row=23, column=0, padx=20, pady=(0, 16), sticky="sw")

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        topbar = ctk.CTkFrame(main, fg_color=theme.SURFACE, corner_radius=0, height=64)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_propagate(False)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(topbar, placeholder_text="Buscar juego...",
                     textvariable=self._search_var, font=theme.FONT_BODY,
                     height=38, corner_radius=20,
                     fg_color=theme.SURFACE_VARIANT, border_color=theme.OUTLINE_VARIANT,
                     text_color=theme.ON_SURFACE).grid(
                     row=0, column=0, padx=20, pady=13, sticky="ew")

        self._status_label = ctk.CTkLabel(
            topbar, text="", font=theme.FONT_LABEL, text_color=theme.PRIMARY_LIGHT)
        self._status_label.grid(row=0, column=1, padx=(0, 20))

        # Update banner (hidden by default, shown in row=1 when update available)
        self._update_banner = ctk.CTkFrame(
            main, fg_color="#1a3a1a", corner_radius=0, height=36)
        self._update_banner.grid_columnconfigure(0, weight=1)
        # Not gridded yet — shown dynamically when update is found.

        self._scroll_frame = ctk.CTkScrollableFrame(
            main, fg_color="transparent",
            scrollbar_button_color=theme.OUTLINE_VARIANT)
        self._scroll_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)

        self._empty_label = ctk.CTkLabel(
            self._scroll_frame,
            text="No hay juegos.\nEscanea una carpeta o vincula tus cuentas desde el panel izquierdo.",
            font=theme.FONT_HEADLINE, text_color=theme.OUTLINE, justify="center")

    # ── Update check ──────────────────────────────────────────────────────────

    def _on_update_found(self, info: dict):
        """Called from background thread — marshal to UI thread."""
        self.after(0, lambda: self._show_update_banner(info))

    def _show_update_banner(self, info: dict):
        """Display a slim banner under the topbar with update info."""
        tag = info["tag"]
        url = info["url"]

        # Populate banner
        ctk.CTkLabel(
            self._update_banner,
            text=f"Nueva version disponible: {tag}  (actual: {info['current']})",
            font=theme.FONT_LABEL,
            text_color="#90ee90",
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=6, sticky="w")

        ctk.CTkButton(
            self._update_banner,
            text="Descargar",
            font=theme.FONT_LABEL,
            width=90, height=24,
            corner_radius=6,
            fg_color=theme.PRIMARY,
            text_color=theme.ON_PRIMARY,
            command=lambda: webbrowser.open(url),
        ).grid(row=0, column=1, padx=(0, 8), pady=4)

        ctk.CTkButton(
            self._update_banner,
            text="x",
            font=theme.FONT_LABEL,
            width=28, height=24,
            corner_radius=6,
            fg_color="transparent",
            text_color="#90ee90",
            hover_color="#2a4a2a",
            command=self._hide_update_banner,
        ).grid(row=0, column=2, padx=(0, 8), pady=4)

        self._update_banner.grid(row=1, column=0, sticky="ew")
        self._update_banner.grid_propagate(False)

    def _hide_update_banner(self):
        self._update_banner.grid_remove()

    # ── Grid rendering — TWO-PHASE ────────────────────────────────────────────

    def _rebuild_cards_for_filter(self):
        for card in self._all_cards:
            card.destroy()
        self._all_cards.clear()
        self._visible_cards.clear()
        self._last_columns = 0

        games = self.game_manager.filter_by_platform(self._current_filter)
        self._count_label.configure(text=f"{len(self.game_manager.games)} juego(s)")

        for game in games:
            card = GameCard(self._scroll_frame, game=game,
                            on_launch=self._launch_game, on_delete=self._delete_game)
            self._all_cards.append(card)

        self._apply_search_filter()

    def _apply_search_filter(self):
        self._empty_label.grid_remove()

        q = self._search_query.lower()
        visible = [c for c in self._all_cards if not q or q in c.game.name.lower()]
        self._visible_cards = visible

        n = len(visible)
        columns = min(self._calc_columns(), n) if n > 0 else 1

        self._set_column_weights(columns)
        self._last_columns = columns

        for i, card in enumerate(visible):
            r, c = divmod(i, columns)
            card.grid(row=r, column=c, padx=8, pady=(12, 8), sticky="nw")

        for card in set(self._all_cards) - set(visible):
            card.grid_remove()

        if not visible:
            self._empty_label.grid(row=0, column=0,
                                   columnspan=max(columns, 1), pady=80, padx=20)

    def _relayout(self):
        if not self._visible_cards:
            return
        n = len(self._visible_cards)
        columns = min(self._calc_columns(), n)
        if columns == self._last_columns:
            return
        self._set_column_weights(columns)
        self._last_columns = columns
        for i, card in enumerate(self._visible_cards):
            r, c = divmod(i, columns)
            card.grid(row=r, column=c, padx=8, pady=(12, 8), sticky="nw")

    def _relayout_force(self):
        """Relayout ignoring cached column count (called once after first render)."""
        if not self._visible_cards:
            return
        saved = self._last_columns
        self._last_columns = 0
        self._relayout()
        if self._last_columns == 0:
            self._last_columns = saved

    def _set_column_weights(self, columns: int):
        prev = self._last_columns
        max_col = max(columns, prev) + 4
        for col in range(max_col):
            self._scroll_frame.grid_columnconfigure(col, weight=0, minsize=0)
        # Spacer column absorbs remaining space; card columns have no minsize.
        self._scroll_frame.grid_columnconfigure(columns, weight=1, minsize=0)

    def _calc_columns(self) -> int:
        # Prefer the inner canvas width — avoids double-counting the scrollbar.
        try:
            w = self._scroll_frame._parent_canvas.winfo_width()
        except Exception:
            w = 0
        if w <= 1:
            w = self._scroll_frame.winfo_width()
        if w <= 1:
            # Fallback before window is fully rendered — be conservative.
            w = self.winfo_width() - 260
        # Scrollbar (~16 px) + inner canvas padding (~20 px) + safety margin.
        usable = max(w - 56, _CARD_CELL)
        return max(1, usable // _CARD_CELL)

    # ── Resize / search ───────────────────────────────────────────────────────

    def _on_resize_debounced(self, event):
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._relayout)

    def _on_search(self, *_args):
        self._search_query = self._search_var.get()
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(80, self._apply_search_filter)

    # ── Filters ───────────────────────────────────────────────────────────────

    def _highlight_filter(self, key: str):
        for k, btn in self._filter_buttons.items():
            btn.configure(
                fg_color=theme.PRIMARY if k == key else "transparent",
                text_color=theme.ON_PRIMARY if k == key else theme.ON_SURFACE_VARIANT)

    def _set_filter(self, key: str):
        self._current_filter = key
        self._highlight_filter(key)
        self._rebuild_cards_for_filter()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _launch_game(self, game: Game):
        try:
            game.launch()
            self._toast(f"Lanzando {game.name}...")
        except FileNotFoundError:
            messagebox.showerror("Error", f"No se encontro el ejecutable:\n{game.executable}")

    def _delete_game(self, game: Game):
        if messagebox.askyesno("Eliminar", f"Eliminar {game.name} de la lista?"):
            self.game_manager.remove_game(game.id)
            self._rebuild_cards_for_filter()

    def _scan_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de juegos")
        if not folder:
            return
        self._toast("Escaneando carpeta...")
        threading.Thread(target=self._do_scan_folder, args=(folder,), daemon=True).start()

    def _do_scan_folder(self, folder: str):
        games = scan_folder(folder)
        added = self._add_games_batch(games)
        self.after(0, lambda: self._on_scan_done(added, "carpeta"))

    def _open_accounts(self):
        from ui.accounts_dialog import AccountsDialog
        AccountsDialog(self, self.game_manager, on_sync_done=self._on_scan_done)

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        SettingsDialog(self)

    def _on_scan_done(self, added: int, source: str):
        msg = (f"{added} juego(s) agregado(s) desde {source}"
               if added else f"Sin juegos nuevos en {source}")
        self._toast(msg)
        self._rebuild_cards_for_filter()

    def _add_games_batch(self, games: list) -> int:
        added = 0
        for game in games:
            before = len(self.game_manager.games)
            self.game_manager.add_game(game)
            if len(self.game_manager.games) > before:
                added += 1
        return added

    def _toast(self, message: str, duration_ms: int = 3500):
        self._status_label.configure(text=message)
        self.after(duration_ms, lambda: self._status_label.configure(text=""))
