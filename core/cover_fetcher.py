"""Cover image fetcher for Epic and EA games."""

import difflib
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


# ── Epic Games (public GraphQL, no auth) ─────────────────────────────────────

EPIC_GQL = "https://graphql.epicgames.com/graphql"
_EPIC_PREF = [
    "OfferImageTall", "DieselStoreFrontTall", "DieselGameBoxTall",
    "Thumbnail", "DieselGameBox",
]


def fetch_epic_cover(game_name: str) -> Optional[str]:
    safe = game_name.replace('"', " ")
    query = (
        '{"query":"{Catalog{searchStore(category:\\"games/edition/base|bundles/games|editors\\"'
        f',count:1,keywords:\\"{safe}\\")'
        '{elements{keyImages{type,url}}}}}}"}' 
    )
    try:
        req = urllib.request.Request(
            EPIC_GQL, data=query.encode(),
            headers={"Content-Type": "application/json", "User-Agent": "GameManager/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        elements = (data.get("data", {}).get("Catalog", {})
                    .get("searchStore", {}).get("elements", []))
        if not elements:
            return None
        images = elements[0].get("keyImages", [])
        for pref in _EPIC_PREF:
            for img in images:
                if img.get("type") == pref and img.get("url"):
                    return img["url"]
        return images[0].get("url") if images else None
    except Exception:
        return None


# ── EA App covers ─────────────────────────────────────────────────────────────
# Priority order:
#  1. Local EA Desktop catalog JSON files (contain CDN image URLs)
#  2. EA store API by content ID
#  3. Local image files in install / cache directories

_EA_CATALOG_ROOTS = [
    Path(r"C:\ProgramData\Electronic Arts\EA Desktop\Catalog"),
    Path(r"C:\ProgramData\EA Desktop\Catalog"),
]
_EA_LOCAL_IMG_NAMES = ["cover", "thumbnail", "box", "header", "poster",
                       "tile", "square"]
_EA_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Build a name→URL cache from local EA catalog JSON files (done once per session)
_ea_catalog_cache: Optional[dict[str, str]] = None


def _build_ea_catalog_cache() -> dict[str, str]:
    global _ea_catalog_cache
    if _ea_catalog_cache is not None:
        return _ea_catalog_cache
    cache: dict[str, str] = {}
    for root in _EA_CATALOG_ROOTS:
        if not root.exists():
            continue
        for jf in root.rglob("*.json"):
            try:
                data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
                name = (data.get("displayName") or data.get("title")
                        or data.get("localizedDisplayName") or "").strip().lower()
                if not name:
                    continue
                # Look for image URLs in common fields
                url = (_extract_image_url(data.get("images", []))
                       or _extract_image_url(data.get("keyImages", []))
                       or data.get("boxArtUrl") or data.get("tileImageUrl")
                       or data.get("coverArtUrl") or "")
                if url and name:
                    cache[name] = url
            except Exception:
                continue
    _ea_catalog_cache = cache
    return cache


def _extract_image_url(images: list) -> Optional[str]:
    if not isinstance(images, list):
        return None
    preferred = {"cover", "box", "tile", "packshot", "coverart"}
    for img in images:
        if not isinstance(img, dict):
            continue
        t = (img.get("type") or img.get("role") or "").lower()
        url = img.get("url") or img.get("src") or ""
        if any(p in t for p in preferred) and url:
            return url
    for img in images:
        if isinstance(img, dict):
            url = img.get("url") or img.get("src") or ""
            if url:
                return url
    return None


def fetch_ea_cover(game_name: str, content_id: str = "",
                   install_path: str = "") -> Optional[str]:
    """Return a cover image URL or local path for an EA game."""

    # 1. Local catalog JSON cache
    catalog = _build_ea_catalog_cache()
    name_lower = game_name.lower()
    # Exact match first, then partial
    url = catalog.get(name_lower)
    if not url:
        for k, v in catalog.items():
            if name_lower in k or k in name_lower:
                url = v
                break
    if url:
        return url

    # 2. Local files in install dir and EA cache dirs.
    # (The old Origin APIs, api2.origin.com, were shut down: calling them only
    # added timeouts. The Steam store fallback covers most EA games.)
    return find_ea_cover_local(install_path, game_name)


def find_ea_cover_local(install_path: str, game_name: str) -> Optional[str]:
    """Scan local directories for EA game artwork."""
    # Install directory
    if install_path:
        img = _scan_dir_for_image(Path(install_path))
        if img:
            return img

    # EA cache / catalog roots
    slug = game_name.lower().replace(" ", "").replace(":", "").replace("-", "")
    for root in _EA_CATALOG_ROOTS:
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            entry_slug = entry.name.lower().replace(" ", "").replace("-", "")
            if slug in entry_slug or entry_slug in slug:
                img = _scan_dir_for_image(entry)
                if img:
                    return img
    return None


def _scan_dir_for_image(directory: Path) -> Optional[str]:
    if not directory.exists():
        return None
    for name in _EA_LOCAL_IMG_NAMES:
        for ext in _EA_IMG_EXTS:
            p = directory / f"{name}{ext}"
            if p.exists():
                return str(p)
    # Any image at root level
    for item in sorted(directory.iterdir()):
        if item.is_file() and item.suffix.lower() in _EA_IMG_EXTS:
            return str(item)
    return None


# ── GOG (public API, no auth) ─────────────────────────────────────────────────

def fetch_gog_cover(product_id: str) -> Optional[str]:
    """Vertical box art from the public GOG API; falls back to the wide logo."""
    if not product_id or not str(product_id).isdigit():
        return None
    headers = {"User-Agent": "GameManager/1.1", "Accept": "application/json"}
    try:
        req = urllib.request.Request(
            f"https://api.gog.com/v2/games/{product_id}?locale=en-US", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        href = data.get("_links", {}).get("boxArtImage", {}).get("href")
        if href:
            return href
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            f"https://api.gog.com/products/{product_id}", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        logo = data.get("images", {}).get("logo2x") or data.get("images", {}).get("logo")
        if logo:
            return "https:" + logo if logo.startswith("//") else logo
    except Exception:
        pass
    return None


# ── Steam store search (public, no key) — fallback for every store ─────────────
# Most EA and many Epic/GOG/Xbox games are also on Steam, whose CDN has
# good vertical box art. Matching is by name, so it's strict to avoid
# showing the wrong game.

_STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/?term={q}&l=english&cc=US"
_STEAM_ART = [
    "https://cdn.akamai.steamstatic.com/steam/apps/{id}/library_600x900_2x.jpg",
    "https://cdn.akamai.steamstatic.com/steam/apps/{id}/library_600x900.jpg",
    "https://cdn.akamai.steamstatic.com/steam/apps/{id}/header.jpg",
]


def _normalize(name: str) -> str:
    # Before NFKD (which turns ™ into "TM"); EA also writes them as "(TM)"/"(R)".
    name = re.sub(r"[™®©]|\((tm|r|c)\)", "", name, flags=re.IGNORECASE)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    name = re.sub(r"\b(standard|deluxe|gold|ultimate|complete|definitive|edition|"
                  r"game of the year|goty|remastered)\b", " ", name)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name).split())


def _url_exists(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "GameManager/1.1"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.status == 200
    except Exception:
        return False


def fetch_steam_cover_by_name(game_name: str) -> Optional[str]:
    target = _normalize(game_name)
    if not target:
        return None
    try:
        url = _STEAM_SEARCH.format(q=urllib.parse.quote(game_name))
        req = urllib.request.Request(url, headers={"User-Agent": "GameManager/1.1"})
        with urllib.request.urlopen(req, timeout=8) as r:
            items = json.loads(r.read()).get("items", [])
    except Exception:
        return None

    numbers = re.findall(r"\d+", target)
    best_id, best_score = None, 0.0
    for item in items:
        candidate = _normalize(item.get("name", ""))
        if candidate == target:
            best_id, best_score = item.get("id"), 1.0
            break
        # Sequels differ only by a number ("FIFA 22" vs "FIFA 23"): never mix them.
        if re.findall(r"\d+", candidate) != numbers:
            continue
        score = difflib.SequenceMatcher(None, target, candidate).ratio()
        if score > best_score:
            best_id, best_score = item.get("id"), score
    if not best_id or best_score < 0.9:
        return None
    for template in _STEAM_ART:
        art = template.format(id=best_id)
        if _url_exists(art):
            return art
    return None


def fetch_cover_for_hint(hint) -> Optional[str]:
    """Resolve a Game.cover_fetch_hint to a cover URL or local path."""
    if not hint:
        return None
    kind = hint[0]
    name = str(hint[1]) if len(hint) > 1 else ""
    found = None
    try:
        if kind == "epic":
            # Epic's public GraphQL is now behind bot protection and only times
            # out, so Epic games go straight to the Steam fallback below.
            found = None
        elif kind == "ea":
            install = hint[2] if len(hint) > 2 else ""
            content_id = hint[3] if len(hint) > 3 else ""
            found = fetch_ea_cover(name, content_id, install)
        elif kind == "gog":
            found = fetch_gog_cover(name)
            name = str(hint[2]) if len(hint) > 2 else ""  # GOG hints: ("gog", id, name)
    except Exception:
        found = None
    if found:
        return found
    # Store-specific lookups failed (Epic's API is now protected, EA moved
    # its catalog): fall back to the matching game on the Steam store.
    return fetch_steam_cover_by_name(name) if name else None
