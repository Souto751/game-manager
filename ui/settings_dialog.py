"""Settings dialog — language and theme preferences."""

import customtkinter as ctk
from core.config_manager import ConfigManager
from ui import theme

_THEMES = {"Oscuro": "dark", "Claro": "light", "Sistema": "system"}
_THEMES_INV = {v: k for k, v in _THEMES.items()}
_LANGS = {"Espanol": "es", "English": "en"}
_LANGS_INV = {v: k for k, v in _LANGS.items()}


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuracion")
        self.geometry("560x380")
        self.resizable(False, False)
        self.configure(fg_color=theme.BACKGROUND)
        self.transient(parent)
        self.grab_set()
        self._cfg = ConfigManager()
        self._parent = parent
        self._build()
        self.after(50, self.lift)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Configuracion", font=theme.FONT_HEADLINE,
                     text_color=theme.PRIMARY_LIGHT, anchor="w").grid(
                     row=0, column=0, padx=24, pady=14, sticky="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=theme.OUTLINE_VARIANT)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Apariencia ────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="APARIENCIA", font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(20, 6), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text="Tema", font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 6), sticky="w")
        row += 1

        current_theme = _THEMES_INV.get(self._cfg.get("theme"), "Oscuro")
        self._theme_seg = ctk.CTkSegmentedButton(
            scroll, values=list(_THEMES.keys()),
            font=theme.FONT_BODY, height=36,
            fg_color=theme.SURFACE_VARIANT,
            selected_color=theme.PRIMARY,
            selected_hover_color=theme.PRIMARY_DARK,
            unselected_color=theme.SURFACE_VARIANT,
            unselected_hover_color=theme.SURFACE_CONTAINER_HIGH,
            text_color=theme.ON_SURFACE,
            command=self._on_theme_change)
        self._theme_seg.set(current_theme)
        self._theme_seg.grid(row=row, column=0, padx=16, pady=(0, 16), sticky="ew")
        row += 1

        # ── Idioma ────────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="IDIOMA", font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(8, 6), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text="Idioma de la interfaz", font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 6), sticky="w")
        row += 1

        current_lang = _LANGS_INV.get(self._cfg.get("language"), "Espanol")
        self._lang_seg = ctk.CTkSegmentedButton(
            scroll, values=list(_LANGS.keys()),
            font=theme.FONT_BODY, height=36,
            fg_color=theme.SURFACE_VARIANT,
            selected_color=theme.PRIMARY,
            selected_hover_color=theme.PRIMARY_DARK,
            unselected_color=theme.SURFACE_VARIANT,
            unselected_hover_color=theme.SURFACE_CONTAINER_HIGH,
            text_color=theme.ON_SURFACE,
            command=self._on_lang_change)
        self._lang_seg.set(current_lang)
        self._lang_seg.grid(row=row, column=0, padx=16, pady=(0, 6), sticky="ew")
        row += 1

        ctk.CTkLabel(scroll, text="El cambio de idioma se aplica al reiniciar.",
                     font=theme.FONT_CAPTION, text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 20), sticky="w")

    def _on_theme_change(self, label: str):
        mode = _THEMES.get(label, "dark")
        self._cfg.set("theme", mode)
        # Defer to the parent window's event loop — calling set_appearance_mode
        # from inside a modal with grab_set() can stall the UI.
        self._parent.after(10, lambda: ctk.set_appearance_mode(mode))

    def _on_lang_change(self, label: str):
        self._cfg.set("language", _LANGS.get(label, "es"))
