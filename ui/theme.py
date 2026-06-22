"""Material Design color palette and theme constants."""

PRIMARY = "#6750A4"
PRIMARY_DARK = "#4F378B"
PRIMARY_LIGHT = "#EADDFF"
ON_PRIMARY = "#FFFFFF"
SECONDARY = "#625B71"
SECONDARY_CONTAINER = "#E8DEF8"
SURFACE = "#1C1B1F"
SURFACE_VARIANT = "#2B2930"
SURFACE_CONTAINER = "#211F26"
SURFACE_CONTAINER_HIGH = "#2B2930"
ON_SURFACE = "#E6E1E5"
ON_SURFACE_VARIANT = "#CAC4D0"
OUTLINE = "#938F99"
OUTLINE_VARIANT = "#49454F"
ERROR = "#CF6679"
SUCCESS = "#4CAF50"
BACKGROUND = "#141218"
CARD_BG = "#2B2930"
CARD_HOVER = "#332F3A"

PLATFORM_COLORS = {
    "steam":  "#1B2838",
    "epic":   "#2D2D2D",
    "ea":     "#FF6B00",
    "gog":    "#8A208C",
    "custom": "#37474F",
    "scanned":"#37474F",
}
PLATFORM_TEXT = {
    "steam":  "#C7D5E0",
    "epic":   "#FFFFFF",
    "ea":     "#FFFFFF",
    "gog":    "#FFFFFF",
    "custom": "#B0BEC5",
    "scanned":"#B0BEC5",
}

# Fonts — must be assigned after CTk is imported; using tuples here is fine.
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_HEADLINE = ("Segoe UI", 16, "bold")
FONT_BODY     = ("Segoe UI", 13)
FONT_BODY_BOLD= ("Segoe UI", 13, "bold")
FONT_LABEL    = ("Segoe UI", 12)
FONT_CAPTION  = ("Segoe UI", 11)
