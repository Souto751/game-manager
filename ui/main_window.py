"""Main application window."""

import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox
import threading

import customtkinter as ctk

from ui import theme
from ui.dispatch import install as install_dispatch, post
from ui.strings import t
from ui.game_card import GameCard, CARD_WIDTH
from core.game_manager import Game, GameManager
from core.config_manager import ConfigManager
from core.folder_scanner import scan_folder
from core.updater import check_for_updates_async
from core.tray import TrayIcon
from core.paths import resource_path

_CARD_GAP = 10                 # padx/pady around each card
_CARD_CELL = CARD_WIDTH + 2 * _CARD_GAP


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._cfg = ConfigManager()
        self.game_manager = GameManager()
        self._current_filter = "all"
        self._search_query = ""
        self._cards: dict[str, GameCard] = {}   # game id -> card, reused across filters
        self._build_queue: list[Game] = []
        self._build_job = None
        self._visible_cards = []
        self._last_columns = 0
        self._resize_job = None
        self._search_job = None
        self._toast_job = None
        install_dispatch(self)
        self._tray = TrayIcon(tooltip=t("app_name"),
                               on_restore=self._on_tray_restore,
                               on_quit=self._on_tray_quit)

        self._configure_window()
        self._build_ui()
        self._highlight_filter("all")
        self._set_filter("all")
        self.bind("<Configure>", self._on_resize_debounced)
        self.after(200, self._relayout_force)
        self.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
        check_for_updates_async(on_update_available=self._on_update_found)

    # ── Window setup ──────────────────────────────────────────────────────────

    def _configure_window(self):
        ctk.set_appearance_mode(self._cfg.get("theme") or "dark")
        ctk.set_default_color_theme("blue")
        self.title(t("app_name"))
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=theme.BACKGROUND)
        try:
            self.iconbitmap(str(resource_path("assets", "icon.ico")))
        except Exception:
            pass

    # ── System tray ───────────────────────────────────────────────────────────

    def _minimize_to_tray(self):
        """Close-button handler: hide the window instead of quitting, and
        surface a hidden tray icon so the app keeps running in the background."""
        self.withdraw()
        self._tray.show(open_label=t("tray_open"), quit_label=t("tray_quit"))

    def _on_tray_restore(self):
        # Called from the tray thread — hop back to the Tk main thread.
        post(self._restore_window)

    def _restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_tray_quit(self):
        # Called from the tray thread — hop back to the Tk main thread.
        post(self._quit_app)

    def _quit_app(self):
        self._tray.hide()
        self.destroy()

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

        ctk.CTkLabel(sidebar, text=t("app_name"),
                     font=theme.FONT_TITLE, text_color=theme.PRIMARY_LIGHT,
                     anchor="w").grid(row=0, column=0, padx=20, pady=(24, 8), sticky="ew")

        # ── BIBLIOTECA ────────────────────────────────────────────────────────
        ctk.CTkLabel(sidebar, text=t("section_library"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=1, column=0, padx=20, pady=(16, 4), sticky="ew")

        self._filter_buttons = {}
        filters = [
            ("all",    t("filter_all")),
            ("steam",  t("filter_steam")),
            ("epic",   t("filter_epic")),
            ("ea",     t("filter_ea")),
            ("gog",    t("filter_gog")),
            ("xbox",   t("filter_xbox")),
            ("custom", t("filter_custom")),
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
        ctk.CTkLabel(sidebar, text=t("section_add_games"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=10, column=0, padx=20, pady=(0, 4), sticky="ew")

        ctk.CTkButton(sidebar, text=t("scan_folder"), font=theme.FONT_BODY,
                      anchor="w", corner_radius=8, height=38,
                      fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                      text_color=theme.ON_SURFACE_VARIANT,
                      command=self._scan_folder).grid(
                      row=11, column=0, padx=12, pady=2, sticky="ew")

        # ── CUENTAS ───────────────────────────────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.OUTLINE_VARIANT).grid(
            row=13, column=0, padx=16, pady=12, sticky="ew")
        ctk.CTkLabel(sidebar, text=t("section_accounts"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=14, column=0, padx=20, pady=(0, 4), sticky="ew")

        ctk.CTkButton(sidebar, text=t("link_accounts"), font=theme.FONT_BODY,
                      anchor="w", corner_radius=8, height=38,
                      fg_color="transparent", hover_color=theme.SURFACE_VARIANT,
                      text_color=theme.ON_SURFACE_VARIANT,
                      command=self._open_accounts).grid(
                      row=15, column=0, padx=12, pady=2, sticky="ew")

        # ── CONFIGURACION (fixed to bottom) ───────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.OUTLINE_VARIANT).grid(
            row=21, column=0, padx=16, pady=(12, 4), sticky="ew")

        ctk.CTkButton(sidebar, text=t("settings"), font=theme.FONT_BODY,
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
        ctk.CTkEntry(topbar, placeholder_text=t("search_placeholder"),
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
            main, fg_color=("#d4edda", "#1a3a1a"), corner_radius=0, height=36)
        self._update_banner.grid_columnconfigure(0, weight=1)
        # Not gridded yet — shown dynamically when update is found.

        self._scroll_frame = ctk.CTkScrollableFrame(
            main, fg_color="transparent",
            scrollbar_button_color=theme.OUTLINE_VARIANT)
        self._scroll_frame.grid(row=2, column=0, sticky="nsew", padx=(12, 0), pady=0)

        # "Steam · 120 juegos" heading above the grid (row 0 of the scroll frame).
        self._grid_title = ctk.CTkLabel(
            self._scroll_frame, text="", font=theme.FONT_HEADLINE,
            text_color=theme.ON_SURFACE, anchor="w")
        self._grid_title.grid(row=0, column=0, columnspan=50, padx=_CARD_GAP,
                              pady=(16, 2), sticky="w")

        # Empty state label lives in `main` so it can fill the area and centre.
        self._empty_label = ctk.CTkLabel(
            main,
            text=t("no_games_text"),
            font=theme.FONT_HEADLINE, text_color=theme.OUTLINE, justify="center")

    # ── Rebuild (called on language change) ───────────────────────────────────

    def _rebuild_ui(self):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        if self._search_job:
            self.after_cancel(self._search_job)
        if self._toast_job:
            self.after_cancel(self._toast_job)
            self._toast_job = None
        if self._build_job:
            self.after_cancel(self._build_job)
            self._build_job = None
        for child in self.winfo_children():
            child.destroy()
        self._current_filter = "all"
        self._search_query = ""
        self._cards: dict[str, GameCard] = {}   # game id -> card, reused across filters
        self._build_queue: list[Game] = []
        self._build_job = None
        self._visible_cards = []
        self._last_columns = 0
        self._resize_job = None
        self._search_job = None
        self._build_ui()
        self._highlight_filter("all")
        self._set_filter("all")
        self.bind("<Configure>", self._on_resize_debounced)
        self.after(200, self._relayout_force)

    # ── Update check ──────────────────────────────────────────────────────────

    def _on_update_found(self, info: dict):
        # Runs on the updater thread.
        post(self._show_update_banner, info)

    def _show_update_banner(self, info: dict):
        tag = info["tag"]
        url = info["url"]

        ctk.CTkLabel(
            self._update_banner,
            text=t("update_available", tag=tag, current=info["current"]),
            font=theme.FONT_LABEL,
            text_color=("#155724", "#90ee90"),
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=6, sticky="w")

        ctk.CTkButton(
            self._update_banner,
            text=t("download"),
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
            text_color=("#155724", "#90ee90"),
            hover_color=("#c3e6cb", "#2a4a2a"),
            command=self._hide_update_banner,
        ).grid(row=0, column=2, padx=(0, 8), pady=4)

        self._update_banner.grid(row=1, column=0, sticky="ew")
        self._update_banner.grid_propagate(False)

    def _hide_update_banner(self):
        self._update_banner.grid_remove()

    # ── Grid rendering — TWO-PHASE ────────────────────────────────────────────

    # Cards are created once per game and reused: changing filter or search
    # only shows/hides them. New cards are built in small batches so the
    # window paints right away instead of freezing on big libraries.
    _BUILD_BATCH = 24

    def _rebuild_cards_for_filter(self):
        """Sync cards with the library (after filter change, import or delete)."""
        library_ids = {g.id for g in self.game_manager.games}
        for game_id in [gid for gid in self._cards if gid not in library_ids]:
            self._cards.pop(game_id).destroy()

        self._count_label.configure(
            text=t("count_label", n=len(self.game_manager.games)))

        # Build the cards of the current filter first, then the rest.
        pending = [g for g in self.game_manager.games if g.id not in self._cards]
        in_view = set(id(g) for g in self.game_manager.filter_by_platform(self._current_filter))
        pending.sort(key=lambda g: id(g) not in in_view)
        self._build_queue = pending

        if self._build_job:
            self.after_cancel(self._build_job)
            self._build_job = None
        self._build_batch(first=True)

    def _build_batch(self, first: bool = False):
        self._build_job = None
        batch, self._build_queue = (self._build_queue[:self._BUILD_BATCH],
                                    self._build_queue[self._BUILD_BATCH:])
        for game in batch:
            self._cards[game.id] = GameCard(
                self._scroll_frame, game=game,
                on_launch=self._launch_game, on_delete=self._delete_game,
                on_cover_resolved=self._remember_cover)
        self._apply_search_filter(scroll_top=first)
        if self._build_queue:
            self._build_job = self.after(15, self._build_batch)

    def _remember_cover(self, game: Game, cover: str):
        # Called from a cover worker thread; GameManager is thread-safe.
        self.game_manager.set_cover(game.id, cover)

    def _update_grid_title(self, n: int):
        label = t(f"filter_{self._current_filter}")
        text = f"{label}  ·  {t('games_in_view', n=n)}"
        if self._build_queue:
            # Still creating cards: show progress instead of a frozen-looking grid.
            text += f"   ·   {t('loading_cards', done=len(self._cards), total=len(self.game_manager.games))}"
        self._grid_title.configure(text=text)

    def _scroll_to_top(self):
        # CTkScrollableFrame keeps its old scroll offset when the content shrinks:
        # after scrolling "All games" and switching to a short filter the cards
        # ended up above the viewport with no way to scroll back.
        try:
            self._scroll_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _apply_search_filter(self, scroll_top: bool = True):
        q = self._search_query.lower()
        visible = [self._cards[g.id]
                   for g in self.game_manager.filter_by_platform(self._current_filter)
                   if g.id in self._cards and (not q or q in g.name.lower())]
        self._visible_cards = visible
        still_building = bool(self._build_queue)
        self._update_grid_title(len(visible))

        n = len(visible)
        columns = min(self._calc_columns(), n) if n > 0 else 1
        if columns != self._last_columns:
            self._set_column_weights(columns)
            self._last_columns = columns
        self._place_cards(visible, columns)

        visible_set = set(visible)
        for card in self._cards.values():
            if card not in visible_set and getattr(card, "_grid_pos", None) is not None:
                card.grid_remove()
                card._grid_pos = None

        if scroll_top:
            self._scroll_to_top()

        if not visible and not still_building:
            self._scroll_frame.grid_remove()
            self._empty_label.grid(row=2, column=0, sticky="nsew")
        else:
            self._empty_label.grid_remove()
            self._scroll_frame.grid(row=2, column=0, sticky="nsew", padx=(12, 0), pady=0)

    def _place_cards(self, cards: list, columns: int):
        """Grid cards in order, skipping the ones already in the right cell."""
        for i, card in enumerate(cards):
            r, c = divmod(i, columns)
            pos = (r + 1, c)
            if getattr(card, "_grid_pos", None) != pos:
                card.grid(row=pos[0], column=pos[1], padx=_CARD_GAP, pady=_CARD_GAP, sticky="nw")
                card._grid_pos = pos

    def _relayout(self):
        if not self._visible_cards:
            return
        n = len(self._visible_cards)
        columns = min(self._calc_columns(), n)
        if columns == self._last_columns:
            return
        self._set_column_weights(columns)
        self._last_columns = columns
        self._place_cards(self._visible_cards, columns)

    def _relayout_force(self):
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
        self._scroll_frame.grid_columnconfigure(columns, weight=1, minsize=0)

    def _calc_columns(self) -> int:
        try:
            w = self._scroll_frame._parent_canvas.winfo_width()
        except Exception:
            w = 0
        if w <= 1:
            w = self._scroll_frame.winfo_width()
        if w <= 1:
            w = self.winfo_width() - 260
        # winfo_width() is in real pixels, but CustomTkinter scales every widget
        # by the Windows display scaling (e.g. 125%). Compare like with like,
        # otherwise the last column overflows and gets cut off on the right.
        try:
            scale = ctk.ScalingTracker.get_widget_scaling(self._scroll_frame)
        except Exception:
            scale = 1.0
        cell = _CARD_CELL * scale
        usable = w - 24 * scale  # scrollbar + a little breathing room
        return max(1, int(usable // cell))

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
            self._toast(t("launching", name=game.name))
        except FileNotFoundError:
            messagebox.showerror(
                "Error", t("exe_not_found", path=game.executable))

    def _delete_game(self, game: Game):
        if messagebox.askyesno(t("delete_title"), t("delete_msg", name=game.name)):
            self.game_manager.remove_game(game.id)
            self._rebuild_cards_for_filter()

    def _scan_folder(self):
        folder = filedialog.askdirectory(title=t("scan_folder"))
        if not folder:
            return
        self._toast(t("scanning"))
        threading.Thread(target=self._do_scan_folder, args=(folder,), daemon=True).start()

    def _do_scan_folder(self, folder: str):
        # Runs on a worker thread.
        try:
            added = self.game_manager.add_games(scan_folder(folder))
        except Exception:
            added = 0
        post(self._on_scan_done, added, t("scan_folder"))

    def _open_accounts(self):
        from ui.accounts_dialog import AccountsDialog
        AccountsDialog(self, self.game_manager, on_sync_done=self._on_scan_done)

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        SettingsDialog(self)

    def _on_scan_done(self, added: int, source: str):
        msg = (t("added_from", n=added, source=source)
               if added else t("no_new_from", source=source))
        self._toast(msg)
        self._rebuild_cards_for_filter()

    def _toast(self, message: str, duration_ms: int = 3500):
        # Cancel the previous timer so it can't erase this newer message early.
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._status_label.configure(text=message)
        self._toast_job = self.after(duration_ms, self._clear_toast)

    def _clear_toast(self):
        self._toast_job = None
        self._status_label.configure(text="")
