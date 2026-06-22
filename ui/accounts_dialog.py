"""Accounts dialog — link platform accounts and sync game libraries."""

import threading
import customtkinter as ctk
from core.account_manager import AccountManager
from ui import theme

_BTN = dict(font=theme.FONT_LABEL, height=34, corner_radius=20,
            text_color=theme.ON_PRIMARY)


class AccountsDialog(ctk.CTkToplevel):
    def __init__(self, parent, game_manager=None, on_sync_done=None):
        super().__init__(parent)
        self.title("Vincular cuentas")
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
        ctk.CTkLabel(header, text="Vincular cuentas", font=theme.FONT_HEADLINE,
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

        desc = ("Inicia sesion con tu cuenta de Steam en el navegador.\n"
                "Se importara tu biblioteca completa (perfil debe ser publico).")
        ctk.CTkLabel(card, text=desc, font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._steam_status = self._status_label(card, 1)
        self._update_steam_status()

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")

        self._steam_connect_btn = ctk.CTkButton(
            btn_frame, text="Conectar con Steam",
            fg_color="#1B2838", hover_color="#2a475e",
            command=self._connect_steam, **_BTN)
        self._steam_connect_btn.pack(side="left", padx=(0, 8))

        if self._am.steam_id:
            ctk.CTkButton(btn_frame, text="Sincronizar biblioteca",
                          fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_DARK,
                          command=self._sync_steam, **_BTN).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_frame, text="Desvincular",
                          fg_color=theme.SURFACE_CONTAINER_HIGH,
                          hover_color=theme.ERROR,
                          text_color=theme.ON_SURFACE_VARIANT,
                          font=theme.FONT_LABEL, height=34, corner_radius=20,
                          command=self._unlink_steam).pack(side="left")

        # ── Epic Games ────────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "EPIC GAMES", "#2D2D2D", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        desc = ("Epic Games importa los juegos instalados desde el launcher local.\n"
                "No se requiere inicio de sesion adicional.")
        ctk.CTkLabel(card, text=desc, font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._epic_status = self._status_label(card, 1)
        self._update_epic_status()

        btn_frame2 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame2.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._epic_btn = ctk.CTkButton(
            btn_frame2, text="Detectar juegos de Epic",
            fg_color=theme.SURFACE_CONTAINER_HIGH,
            hover_color=theme.OUTLINE_VARIANT,
            text_color=theme.ON_SURFACE, font=theme.FONT_LABEL,
            height=34, corner_radius=20,
            command=self._connect_epic)
        self._epic_btn.pack(side="left")

        # ── EA App ────────────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "EA APP", "#FF6B00", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        desc = ("EA App importa los juegos instalados leyendo los datos locales\n"
                "del cliente EA en tu sistema.")
        ctk.CTkLabel(card, text=desc, font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._ea_status = self._status_label(card, 1)
        self._update_ea_status()

        btn_frame3 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame3.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._ea_btn = ctk.CTkButton(
            btn_frame3, text="Detectar juegos de EA",
            fg_color="#FF6B00", hover_color="#cc5500",
            text_color="#FFFFFF", font=theme.FONT_LABEL,
            height=34, corner_radius=20,
            command=self._connect_ea)
        self._ea_btn.pack(side="left")

        # ── Xbox Game Pass ────────────────────────────────────────────────────
        r = self._section_title(scroll, r, "XBOX GAME PASS", "#107C10", "#FFFFFF")
        card = self._card(scroll, r); r += 1
        card.grid_columnconfigure(0, weight=1)

        desc = ("Detecta los juegos de Xbox Game Pass instalados en tu PC\n"
                "desde la app de Xbox (carpeta XboxGames y registro de Windows).")
        ctk.CTkLabel(card, text=desc, font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE_VARIANT, anchor="w",
                     justify="left", wraplength=540).grid(
                     row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._xbox_status = self._status_label(card, 1)
        self._update_xbox_status()

        btn_frame4 = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame4.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="w")
        self._xbox_btn = ctk.CTkButton(
            btn_frame4, text="Detectar juegos de Xbox",
            fg_color="#107C10", hover_color="#0a5a0a",
            text_color="#FFFFFF", font=theme.FONT_LABEL,
            height=34, corner_radius=20,
            command=self._connect_xbox)
        self._xbox_btn.pack(side="left")

        # Bottom spacer
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
                text=f"Conectado  •  Steam ID: {sid}", text_color=theme.SUCCESS)
        else:
            self._steam_status.configure(
                text="No conectado", text_color=theme.OUTLINE)

    def _update_epic_status(self):
        from pathlib import Path
        manifests = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")
        count = len(list(manifests.glob("*.item"))) if manifests.exists() else 0
        if count:
            self._epic_status.configure(
                text=f"Epic Games detectado  •  {count} juego(s) en manifiestos",
                text_color=theme.SUCCESS)
        else:
            self._epic_status.configure(
                text="Epic Games Launcher no encontrado", text_color=theme.OUTLINE)

    def _update_ea_status(self):
        from pathlib import Path
        ea_dir = Path(r"C:\ProgramData\EA Desktop\InstallData")
        count = len(list(ea_dir.rglob("*.json"))) if ea_dir.exists() else 0
        if count:
            self._ea_status.configure(
                text=f"EA App detectada  •  {count} archivo(s) de instalacion",
                text_color=theme.SUCCESS)
        else:
            self._ea_status.configure(
                text="EA App no encontrada en la ruta por defecto", text_color=theme.OUTLINE)

    def _update_xbox_status(self):
        from pathlib import Path
        xbox_dir = Path(r"C:\XboxGames")
        count = sum(1 for e in xbox_dir.iterdir() if e.is_dir()) if xbox_dir.exists() else 0
        if count:
            self._xbox_status.configure(
                text=f"Xbox Game Pass detectado  •  {count} juego(s) en XboxGames",
                text_color=theme.SUCCESS)
        else:
            self._xbox_status.configure(
                text="Carpeta XboxGames no encontrada", text_color=theme.OUTLINE)

    # ── Connect handlers ──────────────────────────────────────────────────────

    def _connect_steam(self):
        """Open Steam login in browser, wait for OpenID callback, then sync."""
        self._steam_connect_btn.configure(state="disabled",
                                          text="Esperando autenticacion...")
        self._steam_status.configure(
            text="Abriendo Steam en el navegador — inicia sesion y autoriza.",
            text_color=theme.OUTLINE)
        threading.Thread(target=self._do_steam_auth, daemon=True).start()

    def _do_steam_auth(self):
        try:
            from core.steam_auth import authenticate
            steam_id = authenticate()
        except Exception as e:
            self.after(0, lambda: self._on_steam_done(None, str(e)))
            return
        self.after(0, lambda: self._on_steam_done(steam_id, None))

    def _on_steam_done(self, steam_id, error):
        self._steam_connect_btn.configure(state="normal", text="Conectar con Steam")
        if error or not steam_id:
            self._set_status(self._steam_status,
                             error or "Autenticacion cancelada o tiempo agotado.", ok=False)
            return
        self._am.save_steam("", steam_id)
        self._update_steam_status()
        self._sync_steam()

    def _sync_steam(self):
        """Fetch game library for the stored Steam ID."""
        sid = self._am.steam_id
        if not sid:
            return
        self._set_status(self._steam_status, "Importando biblioteca de Steam...", ok=True)
        threading.Thread(target=self._do_steam_sync, args=(sid,), daemon=True).start()

    def _do_steam_sync(self, steam_id: str):
        games, error = [], None
        try:
            # Installed games (local ACF manifests)
            from core.steam_detector import detect_steam_games
            games.extend(detect_steam_games())
            # Full cloud library (public profile XML)
            from core.steam_local_library import fetch_library_by_steam_id
            games.extend(fetch_library_by_steam_id(steam_id))
        except PermissionError as e:
            error = str(e)
        except Exception as e:
            error = f"Error al importar: {e}"
        added = self._bulk_add(games)
        self.after(0, lambda: self._on_steam_sync_done(added, error))

    def _on_steam_sync_done(self, added: int, error):
        if error:
            self._set_status(self._steam_status, error, ok=False)
        else:
            self._update_steam_status()
            self._steam_status.configure(
                text=self._steam_status.cget("text") + f"  •  {added} juego(s) nuevos importados")
        if self._on_sync_done:
            self._on_sync_done(added, "Steam")

    def _unlink_steam(self):
        self._am.clear("steam")
        self._update_steam_status()

    # ── Epic ──────────────────────────────────────────────────────────────────

    def _connect_epic(self):
        self._epic_btn.configure(state="disabled", text="Detectando...")
        threading.Thread(target=self._do_epic_sync, daemon=True).start()

    def _do_epic_sync(self):
        try:
            from core.epic_reader import detect_epic_games
            games = detect_epic_games()
        except Exception as e:
            self.after(0, lambda: self._on_platform_done(
                self._epic_btn, self._epic_status, 0,
                f"Error: {e}", "Detectar juegos de Epic"))
            return
        added = self._bulk_add(games)
        self.after(0, lambda: self._on_platform_done(
            self._epic_btn, self._epic_status, added, None,
            "Detectar juegos de Epic"))

    # ── EA ────────────────────────────────────────────────────────────────────

    def _connect_ea(self):
        self._ea_btn.configure(state="disabled", text="Detectando...")
        threading.Thread(target=self._do_ea_sync, daemon=True).start()

    def _do_ea_sync(self):
        try:
            from core.ea_reader import detect_ea_games
            games = detect_ea_games()
        except Exception as e:
            self.after(0, lambda: self._on_platform_done(
                self._ea_btn, self._ea_status, 0,
                f"Error: {e}", "Detectar juegos de EA"))
            return
        added = self._bulk_add(games)
        self.after(0, lambda: self._on_platform_done(
            self._ea_btn, self._ea_status, added, None,
            "Detectar juegos de EA"))

    # ── Xbox ──────────────────────────────────────────────────────────────────

    def _connect_xbox(self):
        self._xbox_btn.configure(state="disabled", text="Detectando...")
        threading.Thread(target=self._do_xbox_sync, daemon=True).start()

    def _do_xbox_sync(self):
        try:
            from core.xbox_reader import detect_xbox_games
            games = detect_xbox_games()
        except Exception as e:
            self.after(0, lambda: self._on_platform_done(
                self._xbox_btn, self._xbox_status, 0,
                f"Error: {e}", "Detectar juegos de Xbox"))
            return
        added = self._bulk_add(games)
        self.after(0, lambda: self._on_platform_done(
            self._xbox_btn, self._xbox_status, added, None,
            "Detectar juegos de Xbox"))

    # ── Shared callback ───────────────────────────────────────────────────────

    def _on_platform_done(self, btn, status_lbl, added, error, btn_text):
        btn.configure(state="normal", text=btn_text)
        if error:
            self._set_status(status_lbl, error, ok=False)
        else:
            msg = (f"{added} juego(s) nuevos importados"
                   if added else "Sin juegos nuevos (ya estaban en la biblioteca)")
            self._set_status(status_lbl, msg, ok=True)
        if self._on_sync_done and not error:
            self._on_sync_done(added, btn_text)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _bulk_add(self, games) -> int:
        if not self._gm:
            return 0
        added = 0
        for g in games:
            before = len(self._gm.games)
            self._gm.add_game(g)
            if len(self._gm.games) > before:
                added += 1
        return added
