"""Settings dialog — theme, language and startup preferences."""

import tkinter as tk
import customtkinter as ctk
from core.config_manager import ConfigManager
from core import autostart
from ui import theme
from ui.strings import reload_language, t


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("settings_title"))
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(fg_color=theme.BACKGROUND)
        self.transient(parent)
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
        ctk.CTkLabel(header, text=t("settings_title"), font=theme.FONT_HEADLINE,
                     text_color=theme.PRIMARY_LIGHT, anchor="w").grid(
                     row=0, column=0, padx=24, pady=14, sticky="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=theme.OUTLINE_VARIANT)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Startup ───────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text=t("startup_section"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(20, 6), sticky="w")
        row += 1

        self._autostart_var = tk.IntVar(value=1 if autostart.is_enabled() else 0)
        self._autostart_switch = ctk.CTkSwitch(
            scroll, text=t("start_with_windows_label"),
            font=theme.FONT_BODY, text_color=theme.ON_SURFACE,
            variable=self._autostart_var, onvalue=1, offvalue=0,
            fg_color=theme.SURFACE_VARIANT,
            progress_color=theme.PRIMARY,
            button_hover_color=theme.PRIMARY_DARK,
            command=self._on_autostart_toggle)
        self._autostart_switch.grid(row=row, column=0, padx=20, pady=(0, 6), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text=t("start_with_windows_note"),
                     font=theme.FONT_CAPTION, text_color=theme.OUTLINE, anchor="w",
                     justify="left").grid(
                     row=row, column=0, padx=20, pady=(0, 4), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text=t("minimize_to_tray_note"),
                     font=theme.FONT_CAPTION, text_color=theme.OUTLINE, anchor="w",
                     justify="left").grid(
                     row=row, column=0, padx=20, pady=(0, 20), sticky="w")
        row += 1

        # ── Appearance ────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text=t("appearance"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(20, 6), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text=t("theme_label"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 6), sticky="w")
        row += 1

        # Build theme label ↔ mode mapping in current language
        self._theme_labels = [t("theme_dark"), t("theme_light"), t("theme_system")]
        self._theme_modes  = ["dark", "light", "system"]

        current_mode  = self._cfg.get("theme") or "dark"
        try:
            current_label = self._theme_labels[self._theme_modes.index(current_mode)]
        except ValueError:
            current_label = self._theme_labels[0]

        self._theme_seg = ctk.CTkSegmentedButton(
            scroll, values=self._theme_labels,
            font=theme.FONT_BODY, height=36,
            fg_color=theme.SURFACE_VARIANT,
            selected_color=theme.PRIMARY,
            selected_hover_color=theme.PRIMARY_DARK,
            unselected_color=theme.SURFACE_VARIANT,
            unselected_hover_color=theme.SURFACE_CONTAINER_HIGH,
            text_color=theme.ON_SURFACE,
            command=self._on_theme_change)
        self._theme_seg.set(current_label)
        self._theme_seg.grid(row=row, column=0, padx=16, pady=(0, 16), sticky="ew")
        row += 1

        # ── Language ──────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text=t("language_section"), font=theme.FONT_CAPTION,
                     text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(8, 6), sticky="w")
        row += 1

        ctk.CTkLabel(scroll, text=t("language_label"), font=theme.FONT_BODY,
                     text_color=theme.ON_SURFACE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 6), sticky="w")
        row += 1

        self._lang_labels = [t("lang_spanish"), t("lang_english")]
        self._lang_codes  = ["es", "en"]

        current_lang = self._cfg.get("language") or "es"
        try:
            current_lang_label = self._lang_labels[self._lang_codes.index(current_lang)]
        except ValueError:
            current_lang_label = self._lang_labels[0]

        self._lang_seg = ctk.CTkSegmentedButton(
            scroll, values=self._lang_labels,
            font=theme.FONT_BODY, height=36,
            fg_color=theme.SURFACE_VARIANT,
            selected_color=theme.PRIMARY,
            selected_hover_color=theme.PRIMARY_DARK,
            unselected_color=theme.SURFACE_VARIANT,
            unselected_hover_color=theme.SURFACE_CONTAINER_HIGH,
            text_color=theme.ON_SURFACE,
            command=self._on_lang_change)
        self._lang_seg.set(current_lang_label)
        self._lang_seg.grid(row=row, column=0, padx=16, pady=(0, 6), sticky="ew")
        row += 1

        ctk.CTkLabel(scroll, text=t("language_note"),
                     font=theme.FONT_CAPTION, text_color=theme.OUTLINE, anchor="w").grid(
                     row=row, column=0, padx=20, pady=(0, 20), sticky="w")

    def _on_autostart_toggle(self):
        enable = self._autostart_var.get() == 1
        ok = autostart.enable() if enable else autostart.disable()
        if not ok:
            # Revert the switch if the registry write failed.
            self._autostart_var.set(0 if enable else 1)
            if enable:
                self._autostart_switch.deselect()
            else:
                self._autostart_switch.select()
            return
        self._cfg.set("start_with_windows", enable)

    def _on_theme_change(self, label: str):
        try:
            mode = self._theme_modes[self._theme_labels.index(label)]
        except (ValueError, IndexError):
            mode = "dark"
        self._cfg.set("theme", mode)
        ctk.set_appearance_mode(mode)

    def _on_lang_change(self, label: str):
        try:
            lang = self._lang_codes[self._lang_labels.index(label)]
        except (ValueError, IndexError):
            lang = "es"
        self._cfg.set("language", lang)
        reload_language()
        # Rebuild the main window UI with the new language strings.
        self.destroy()
        self._parent.after(10, self._parent._rebuild_ui)
