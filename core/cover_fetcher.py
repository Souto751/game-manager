"""Cover image fetcher for Epic and EA games."""

import json
import urllib.request
import urllib.parse
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

    # 2. EA store API by content ID
    if content_id:
        api_url = (_ea_api_cover_by_id(content_id))
        if api_url:
            return api_url

    # 3. Try EA store search API
    store_url = _ea_store_search(game_name)
    if store_url:
        return store_url

    # 4. Local files in install dir and EA cache dirs
    return find_ea_cover_local(install_path, game_name)


def _ea_api_cover_by_id(content_id: str) -> Optional[str]:
    """Try the EA/Origin API for a cover image using the content/software ID."""
    try:
        url = (f"https://api2.origin.com/ecommerce2/products/{content_id}"
               f"/en_US/mobile/medium-tablet.jpg")
        req = urllib.request.Request(
            url, headers={"User-Agent": "GameManager/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            if r.status == 200 and "image" in r.headers.get("Content-Type", ""):
                return url
    except Exception:
        pass
    return None


def _ea_store_search(game_name: str) -> Optional[str]:
    """Search EA store API for a game cover (no auth needed for public titles)."""
    try:
        q = urllib.parse.quote(game_name)
        url = (f"https://api2.origin.com/games/search?searchTerm={q}"
               f"&locale=en_US&start=0&rows=1&sku=PCWIN")
        req = urllib.request.Request(
            url, headers={"User-Agent": "GameManager/1.0",
                          "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        games = data.get("offer", []) or data.get("offers", [])
        if not games:
            return None
        offer = games[0]
        images = offer.get("imageServer", "") 
        img_path = (offer.get("packArtSmall") or offer.get("boxArtSmall")
                    or offer.get("packArtLarge") or "")
        if images and img_path:
            return images.rstrip("/") + "/" + img_path.lstrip("/")
    except Exception:
        pass
    return None


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
