"""Material Design 3 color palette.

All color constants are (light_mode, dark_mode) tuples.
CustomTkinter natively reads these and picks the right value based on
the current appearance mode set via ctk.set_appearance_mode().
"""

# ── Core palette ──────────────────────────────────────────────────────────────
PRIMARY              = ("#6750A4", "#6750A4")
PRIMARY_DARK         = ("#4F378B", "#4F378B")
PRIMARY_LIGHT        = ("#4F378B", "#EADDFF")   # accent text on bg surfaces
ON_PRIMARY           = ("#FFFFFF", "#FFFFFF")

SECONDARY            = ("#625B71", "#625B71")
SECONDARY_CONTAINER  = ("#E8DEF8", "#4A4458")

# ── Surfaces ──────────────────────────────────────────────────────────────────
SURFACE              = ("#F7F2FA", "#1C1B1F")
SURFACE_VARIANT      = ("#E7E0EC", "#2B2930")
SURFACE_CONTAINER    = ("#F3EDF7", "#211F26")
SURFACE_CONTAINER_HIGH = ("#ECE6F0", "#2B2930")

# ── On-surface text ───────────────────────────────────────────────────────────
ON_SURFACE           = ("#1C1B1F", "#E6E1E5")
ON_SURFACE_VARIANT   = ("#49454F", "#CAC4D0")

# ── Outlines ──────────────────────────────────────────────────────────────────
OUTLINE              = ("#79747E", "#938F99")
OUTLINE_VARIANT      = ("#CAC4D0", "#49454F")

# ── Semantic ──────────────────────────────────────────────────────────────────
ERROR                = ("#B3261E", "#CF6679")
SUCCESS              = ("#386A20", "#4CAF50")

# ── Window background ─────────────────────────────────────────────────────────
BACKGROUND           = ("#FFFBFE", "#141218")

# ── Cards ─────────────────────────────────────────────────────────────────────
CARD_BG              = ("#F7F2FA", "#2B2930")
CARD_HOVER           = ("#EDE8F5", "#332F3A")

# ── Platform badge colors (brand-fixed, not themed) ───────────────────────────
PLATFORM_COLORS = {
    "steam":   "#1B2838",
    "epic":    "#2D2D2D",
    "ea":      "#FF6B00",
    "gog":     "#8A208C",
    "xbox":    "#107C10",
    "custom":  "#37474F",
    "scanned": "#37474F",
}
PLATFORM_TEXT = {
    "steam":   "#C7D5E0",
    "epic":    "#FFFFFF",
    "ea":      "#FFFFFF",
    "gog":     "#FFFFFF",
    "xbox":    "#FFFFFF",
    "custom":  "#B0BEC5",
    "scanned": "#B0BEC5",
}

# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE     = ("Segoe UI", 18, "bold")
FONT_HEADLINE  = ("Segoe UI", 16, "bold")
FONT_BODY      = ("Segoe UI", 13)
FONT_BODY_BOLD = ("Segoe UI", 13, "bold")
FONT_LABEL     = ("Segoe UI", 12)
FONT_CAPTION   = ("Segoe UI", 11)
