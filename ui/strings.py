"""UI string translations. All user-visible text goes through t("key")."""

_STRINGS = {
    "es": {
        "app_name":           "Game Manager",
        "section_library":    "BIBLIOTECA",
        "filter_all":         "Todos los juegos",
        "filter_steam":       "Steam",
        "filter_epic":        "Epic Games",
        "filter_ea":          "EA App",
        "filter_gog":         "GOG",
        "filter_xbox":        "Xbox",
        "filter_custom":      "Personalizados",
        "section_add_games":  "AGREGAR JUEGOS",
        "scan_folder":        "Escanear carpeta",
        "section_accounts":   "CUENTAS",
        "link_accounts":      "Vincular cuentas",
        "settings":           "Configuracion",
        "search_placeholder": "Buscar juego...",
        "no_games_text":      "No hay juegos.\nEscanea una carpeta o vincula tus cuentas desde el panel izquierdo.",
        "play":               "Jugar",
        "count_label":        "{n} juego(s)",
        "delete_title":       "Eliminar",
        "delete_msg":         "¿Eliminar {name} de la lista?",
        "remove_from_library": "Quitar de la biblioteca",
        "open_location":      "Abrir ubicacion",
        "more_options":       "Mas opciones",
        "location_not_found": "No se encontro la carpeta del juego.",
        "games_in_view":      "{n} juego(s)",
        "loading_cards":      "cargando {done}/{total}...",
        "launching":          "Lanzando {name}...",
        "exe_not_found":      "No se encontro el ejecutable:\n{path}",
        "scanning":           "Escaneando carpeta...",
        "added_from":         "{n} juego(s) agregado(s) desde {source}",
        "no_new_from":        "Sin juegos nuevos en {source}",
        "update_available":   "Nueva version disponible: {tag}  (actual: {current})",
        "download":           "Descargar",
        "settings_title":     "Configuracion",
        "startup_section":    "INICIO",
        "start_with_windows_label": "Iniciar con Windows",
        "start_with_windows_note": "La app se abrira automaticamente al iniciar sesion en Windows.",
        "minimize_to_tray_note": "Al cerrar la ventana, Game Manager sigue ejecutandose en segundo plano (icono oculto de la bandeja de Windows).",
        "tray_open":          "Abrir Game Manager",
        "tray_quit":          "Salir",
        "appearance":         "APARIENCIA",
        "theme_label":        "Tema",
        "theme_dark":         "Oscuro",
        "theme_light":        "Claro",
        "theme_system":       "Sistema",
        "language_section":   "IDIOMA",
        "language_label":     "Idioma de la interfaz",
        "language_note":      "El cambio de idioma se aplica de inmediato.",
        "lang_spanish":       "Espanol",
        "lang_english":       "English",
        "accounts_title":     "Vincular cuentas",
        "steam_desc":         "Inicia sesion con tu cuenta de Steam en el navegador.\nSe importara tu biblioteca completa (perfil debe ser publico).",
        "steam_connected":    "Conectado  •  Steam ID: {sid}",
        "steam_not_connected":"No conectado",
        "connect_steam":      "Conectar con Steam",
        "sync_library":       "Sincronizar biblioteca",
        "unlink":             "Desvincular",
        "epic_desc":          "Epic Games importa los juegos instalados desde el launcher local.\nNo se requiere inicio de sesion adicional.",
        "detect_epic":        "Detectar juegos de Epic",
        "ea_desc":            "EA App importa los juegos instalados leyendo los datos locales\ndel cliente EA en tu sistema.",
        "detect_ea":          "Detectar juegos de EA",
        "xbox_desc":          "Detecta los juegos de Xbox Game Pass instalados en tu PC\ndesde la app de Xbox (carpeta XboxGames y registro de Windows).",
        "detect_xbox":        "Detectar juegos de Xbox",
        "detecting":          "Detectando...",
        "auth_waiting_btn":   "Esperando autenticacion...",
        "auth_waiting_lbl":   "Abriendo Steam en el navegador — inicia sesion y autoriza.",
        "epic_found":         "Epic Games detectado  •  {count} juego(s) en manifiestos",
        "epic_not_found":     "Epic Games Launcher no encontrado",
        "ea_found":           "EA App detectada  •  {count} archivo(s) de instalacion",
        "ea_not_found":       "EA App no encontrada en la ruta por defecto",
        "xbox_found":         "Xbox Game Pass detectado  •  {count} juego(s) en XboxGames",
        "xbox_not_found":     "Carpeta XboxGames no encontrada",
        "games_imported":     "{n} juego(s) nuevos importados",
        "no_new_games":       "Sin juegos nuevos (ya estaban en la biblioteca)",
        "auth_cancelled":     "Autenticacion cancelada o tiempo agotado.",
        "importing_steam":    "Importando biblioteca de Steam...",
        "steam_synced":       "  •  {n} juego(s) nuevos importados",
    },
    "en": {
        "app_name":           "Game Manager",
        "section_library":    "LIBRARY",
        "filter_all":         "All games",
        "filter_steam":       "Steam",
        "filter_epic":        "Epic Games",
        "filter_ea":          "EA App",
        "filter_gog":         "GOG",
        "filter_xbox":        "Xbox",
        "filter_custom":      "Custom",
        "section_add_games":  "ADD GAMES",
        "scan_folder":        "Scan folder",
        "section_accounts":   "ACCOUNTS",
        "link_accounts":      "Link accounts",
        "settings":           "Settings",
        "search_placeholder": "Search game...",
        "no_games_text":      "No games found.\nScan a folder or link your accounts from the left panel.",
        "play":               "Play",
        "count_label":        "{n} game(s)",
        "delete_title":       "Delete",
        "delete_msg":         "Remove {name} from the list?",
        "remove_from_library": "Remove from library",
        "open_location":      "Open location",
        "more_options":       "More options",
        "location_not_found": "Game folder not found.",
        "games_in_view":      "{n} game(s)",
        "loading_cards":      "loading {done}/{total}...",
        "launching":          "Launching {name}...",
        "exe_not_found":      "Executable not found:\n{path}",
        "scanning":           "Scanning folder...",
        "added_from":         "{n} game(s) added from {source}",
        "no_new_from":        "No new games in {source}",
        "update_available":   "New version available: {tag}  (current: {current})",
        "download":           "Download",
        "settings_title":     "Settings",
        "startup_section":    "STARTUP",
        "start_with_windows_label": "Start with Windows",
        "start_with_windows_note": "The app will open automatically when you sign into Windows.",
        "minimize_to_tray_note": "Closing the window keeps Game Manager running in the background (hidden icon in the Windows tray).",
        "tray_open":          "Open Game Manager",
        "tray_quit":          "Quit",
        "appearance":         "APPEARANCE",
        "theme_label":        "Theme",
        "theme_dark":         "Dark",
        "theme_light":        "Light",
        "theme_system":       "System",
        "language_section":   "LANGUAGE",
        "language_label":     "Interface language",
        "language_note":      "Language change applies immediately.",
        "lang_spanish":       "Espanol",
        "lang_english":       "English",
        "accounts_title":     "Link accounts",
        "steam_desc":         "Sign in with your Steam account in the browser.\nYour full library will be imported (profile must be public).",
        "steam_connected":    "Connected  •  Steam ID: {sid}",
        "steam_not_connected":"Not connected",
        "connect_steam":      "Connect with Steam",
        "sync_library":       "Sync library",
        "unlink":             "Unlink",
        "epic_desc":          "Epic Games imports installed games from the local launcher.\nNo additional sign-in required.",
        "detect_epic":        "Detect Epic games",
        "ea_desc":            "EA App imports installed games by reading local data\nfrom the EA client on your system.",
        "detect_ea":          "Detect EA games",
        "xbox_desc":          "Detects Xbox Game Pass games installed on your PC\nfrom the Xbox app (XboxGames folder and Windows registry).",
        "detect_xbox":        "Detect Xbox games",
        "detecting":          "Detecting...",
        "auth_waiting_btn":   "Waiting for authentication...",
        "auth_waiting_lbl":   "Opening Steam in browser — sign in and authorize.",
        "epic_found":         "Epic Games detected  •  {count} game(s) in manifests",
        "epic_not_found":     "Epic Games Launcher not found",
        "ea_found":           "EA App detected  •  {count} installation file(s)",
        "ea_not_found":       "EA App not found at default path",
        "xbox_found":         "Xbox Game Pass detected  •  {count} game(s) in XboxGames",
        "xbox_not_found":     "XboxGames folder not found",
        "games_imported":     "{n} new game(s) imported",
        "no_new_games":       "No new games (already in library)",
        "auth_cancelled":     "Authentication cancelled or timed out.",
        "importing_steam":    "Importing Steam library...",
        "steam_synced":       "  •  {n} new game(s) imported",
    },
}


_lang_cache: str | None = None


def reload_language() -> None:
    """Call after changing the language setting."""
    global _lang_cache
    _lang_cache = None


def _current_language() -> str:
    # Cached: t() runs for every card, and reading config.json each time made
    # big libraries slow to render.
    global _lang_cache
    if _lang_cache is None:
        from core.config_manager import ConfigManager
        _lang_cache = ConfigManager().get("language") or "es"
    return _lang_cache


def t(key: str, **kwargs) -> str:
    """Return the translated string for the current language config."""
    lang = _current_language()
    bucket = _STRINGS.get(lang, _STRINGS["es"])
    text = bucket.get(key, _STRINGS["es"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
