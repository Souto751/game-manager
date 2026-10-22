"""Accounts dialog — link platform accounts and sync game libraries."""

import threading
import customtkinter as ctk
from core.account_manager import AccountManager
from ui import theme
from ui.dispatch import post
from ui.strings import t


class AccountsDialog(ctk.CTkToplevel):
    def __init__(self, parent, game_manager=None, on_sync_done=None):
        super().__init__(parent)
        self.title(t("accounts_title"))
        self.geometry("640x680")
        self.resizable(False, False)
        self.configure(fg_color=theme.BACKGROUND)
        self.transient(parent)
        self.grab_set()
        self._am = AccountManager()
        self._gm = game_manager
        self._on_sync_done = on_sync_done
        self._build()
        self.after(50, self.lift)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=t("accounts_title"), font=theme.FONT_HEADLINE,
                     text_color=theme.PRIMARY_LIGHT, anchor="w").grid(
                     row=0, column=0, padx=24, pady=14, sticky="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=theme.OUTLINE_VARIANT)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        r = 0

        # ── Steam ─────────────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "STEAM", "#1B2838", "#C7D5E0")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("steam_desc"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._steam_status = self._status_label(card, 1)
        self._update_steam_status()

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")

        self._steam_connect_btn = ctk.CTkButton(
            btn_frame, text=t("connect_steam"),
            font=theme.FONT_LABEL, height=34, corner_radius=20,
            text_color=theme.ON_PRIMARY,
            fg_color="#1B2838", hover_color="#2a475e",
            command=self._connect_steam)
        self._steam_connect_btn.pack(side="left", padx=(0, 8))

        if self._am.steam_id:
            ctk.CTkButton(btn_frame, text=t("sync_library"),
                          font=theme.FONT_LABEL, height=34, corner_radius=20,
                          text_color=theme.ON_PRIMARY,
                          fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_DARK,
                          command=self._sync_steam).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_frame, text=t("unlink"),
                          font=theme.FONT_LABEL, height=34, corner_radius=20,
                          fg_color=theme.SURFACE_CONTAINER_HIGH,
                          hover_color=theme.ERROR,
                          text_color=theme.ON_SURFACE_VARIANT,
                          command=self._unlink_steam).pack(side="left")

        # ── Epic Games ────────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "EPIC GAMES", "#2D2D2D", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("epic_desc"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._epic_status = self._status_label(card, 1)
        self._update_epic_status()

        btn_frame2 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame2.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._epic_btn = ctk.CTkButton(
            btn_frame2, text=t("detect_epic"),
            font=theme.FONT_LABEL, height=34, corner_radius=20,
            fg_color=theme.SURFACE_CONTAINER_HIGH,
            hover_color=theme.OUTLINE_VARIANT,
            text_color=theme.ON_SURFACE,
            command=self._connect_epic)
        self._epic_btn.pack(side="left")

        # ── EA App ────────────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "EA APP", "#FF6B00", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("ea_desc"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._ea_status = self._status_label(card, 1)
        self._update_ea_status()

        btn_frame3 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame3.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._ea_btn = ctk.CTkButton(
            btn_frame3, text=t("detect_ea"),
            font=theme.FONT_LABEL, height=34, corner_radius=20,
            fg_color="#FF6B00", hover_color="#cc5500",
            text_color="#FFFFFF",
            command=self._connect_ea)
        self._ea_btn.pack(side="left")

        # ── Xbox Game Pass ────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "XBOX GAME PASS", "#107C10", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("xbox_desc"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._xbox_status = self._status_label(card, 1)
        self._update_xbox_status()

        btn_frame4 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame4.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._xbox_btn = ctk.CTkButton(
            btn_frame4, text=t("detect_xbox"),
            font=theme.FONT_LABEL, height=34, corner_radius=20,
            fg_color="#107C10", hover_color="#0a5a0a",
            text_color="#FFFFFF",
            command=self._connect_xbox)
        self._xbox_btn.pack(side="left")

        ctk.CTkLabel(scroll, text="").grid(row=r, column=0, pady=8)

    # ── Status helpers ────────────────────────────────────────────────────────

    def _section_title(self, parent, row, text, bg, fg):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, padx=16, pady=(20, 6), sticky="w")
        ctk.CTkLabel(f, text=text, font=theme.FONT_CAPTION,
                     fg_color=bg, text_color=fg,
                     corner_radius=4, padx=8, pady=3).pack(side="left")
        return row + 1

    def _card(self, parent, row):
        card = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=12)
        card.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="ew")
        return card

    def _status_label(self, parent, row):
        lbl = ctk.CTkLabel(parent, text="", font=theme.FONT_CAPTION,
                           text_color=theme.OUTLINE, anchor="w", justify="left")
        lbl.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        return lbl

    def _set_status(self, lbl, text, ok: bool = True):
        lbl.configure(text=text,
                      text_color=theme.SUCCESS if ok else theme.ERROR)

    # ── Status refreshers ─────────────────────────────────────────────────────

    def _update_steam_status(self):
        sid = self._am.steam_id
        if sid:
            self._steam_status.configure(
                text=t("steam_connected", sid=sid), text_color=theme.SUCCESS)
        else:
            self._steam_status.configure(
                text=t("steam_not_connected"), text_color=theme.OUTLINE)

    def _update_epic_status(self):
        from pathlib import Path
        manifests = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")
        count = len(list(manifests.glob("*.item"))) if manifests.exists() else 0
        if count:
            self._epic_status.configure(
                text=t("epic_found", count=count), text_color=theme.SUCCESS)
        else:
            self._epic_status.configure(
                text=t("epic_not_found"), text_color=theme.OUTLINE)

    def _update_ea_status(self):
        from pathlib import Path
        ea_dir = Path(r"C:\ProgramData\EA Desktop\InstallData")
        count = len(list(ea_dir.rglob("*.json"))) if ea_dir.exists() else 0
        if count:
            self._ea_status.configure(
                text=t("ea_found", count=count), text_color=theme.SUCCESS)
        else:
            self._ea_status.configure(
                text=t("ea_not_found"), text_color=theme.OUTLINE)

    def _update_xbox_status(self):
        from pathlib import Path
        xbox_dir = Path(r"C:\XboxGames")
        count = sum(1 for e in xbox_dir.iterdir() if e.is_dir()) if xbox_dir.exists() else 0
        if count:
            self._xbox_status.configure(
                text=t("xbox_found", count=count), text_color=theme.SUCCESS)
        else:
            self._xbox_status.configure(
                text=t("xbox_not_found"), text_color=theme.OUTLINE)

    # ── Connect handlers ──────────────────────────────────────────────────────

    def _connect_steam(self):
        self._steam_connect_btn.configure(state="disabled",
                                          text=t("auth_waiting_btn"))
        self._steam_status.configure(
            text=t("auth_waiting_lbl"), text_color=theme.OUTLINE)
        threading.Thread(target=self._do_steam_auth, daemon=True).start()

    def _do_steam_auth(self):
        # Runs on a worker thread: never touch widgets here, use post().
        try:
            from core.steam_auth import authenticate
            steam_id, error = authenticate(), None
        except Exception as exc:
            steam_id, error = None, str(exc)  # bind now: `exc` is cleared after the except block
        post(self._on_steam_done, steam_id, error)

    def _on_steam_done(self, steam_id, error):
        if not self.winfo_exists():
            if steam_id and not error:
                self._am.save_steam("", steam_id)  # keep the login even if the dialog was closed
            return
        self._steam_connect_btn.configure(state="normal", text=t("connect_steam"))
        if error or not steam_id:
            self._set_status(self._steam_status,
                             error or t("auth_cancelled"), ok=False)
            return
        self._am.save_steam("", steam_id)
        self._update_steam_status()
        self._sync_steam()

    def _sync_steam(self):
        sid = self._am.steam_id
        if not sid:
            return
        self._set_status(self._steam_status, t("importing_steam"), ok=True)
        threading.Thread(target=self._do_steam_sync, args=(sid,), daemon=True).start()

    def _do_steam_sync(self, steam_id: str):
        games, error = [], None
        try:
            from core.steam_detector import detect_steam_games
            games.extend(detect_steam_games())
            from core.steam_local_library import fetch_library_by_steam_id
            games.extend(fetch_library_by_steam_id(steam_id))
        except PermissionError as e:
            error = str(e)
        except Exception as e:
            error = f"Error: {e}"
        added = self._bulk_add(games)
        post(self._on_steam_sync_done, added, error)

    def _on_steam_sync_done(self, added: int, error):
        if not self.winfo_exists():  # dialog closed during the import: still refresh the library
            if self._on_sync_done:
                self._on_sync_done(added, "Steam")
            return
        if error:
            self._set_status(self._steam_status, error, ok=False)
        else:
            self._update_steam_status()
            self._steam_status.configure(
                text=self._steam_status.cget("text") + t("steam_synced", n=added))
        if self._on_sync_done:
            self._on_sync_done(added, "Steam")

    def _unlink_steam(self):
        self._am.clear("steam")
        self._update_steam_status()

    # ── Epic ──────────────────────────────────────────────────────────────────

    def _connect_epic(self):
        self._epic_btn.configure(state="disabled", text=t("detecting"))
        threading.Thread(target=self._do_epic_sync, daemon=True).start()

    def _do_epic_sync(self):
        from core.epic_reader import detect_epic_games
        self._run_detection(detect_epic_games, self._epic_btn, self._epic_status, t("detect_epic"))

    # ── EA ────────────────────────────────────────────────────────────────────

    def _connect_ea(self):
        self._ea_btn.configure(state="disabled", text=t("detecting"))
        threading.Thread(target=self._do_ea_sync, daemon=True).start()

    def _do_ea_sync(self):
        from core.ea_reader import detect_ea_games
        self._run_detection(detect_ea_games, self._ea_btn, self._ea_status, t("detect_ea"))

    # ── Xbox ──────────────────────────────────────────────────────────────────

    def _connect_xbox(self):
        self._xbox_btn.configure(state="disabled", text=t("detecting"))
        threading.Thread(target=self._do_xbox_sync, daemon=True).start()

    def _do_xbox_sync(self):
        from core.xbox_reader import detect_xbox_games
        self._run_detection(detect_xbox_games, self._xbox_btn, self._xbox_status, t("detect_xbox"))

    def _run_detection(self, detect, btn, status_lbl, btn_text):
        """Worker-thread body shared by Epic, EA and Xbox detection."""
        added, error = 0, None
        try:
            added = self._bulk_add(detect())
        except Exception as exc:
            error = f"Error: {exc}"  # bind now: `exc` is cleared after the except block
        post(self._on_platform_done, btn, status_lbl, added, error, btn_text)

    # ── Shared callback ───────────────────────────────────────────────────────

    def _on_platform_done(self, btn, status_lbl, added, error, btn_text):
        if self.winfo_exists():  # the dialog may have been closed during the import
            btn.configure(state="normal", text=btn_text)
            if error:
                self._set_status(status_lbl, error, ok=False)
            else:
                msg = t("games_imported", n=added) if added else t("no_new_games")
                self._set_status(status_lbl, msg, ok=True)
        if self._on_sync_done and not error:
            self._on_sync_done(added, btn_text)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _bulk_add(self, games) -> int:
        if not self._gm:
            return 0
        return self._gm.add_games(games)
