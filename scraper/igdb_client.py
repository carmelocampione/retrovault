"""
scraper/igdb_client.py
IGDB API wrapper.
- Haalt automatisch een OAuth token op via Twitch
- Token wordt gecached in config/igdb_token.json
- Zoekt games op naam + platform
- Downloadt cover art
"""

import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error


# IGDB platform IDs voor onze consoles
PLATFORM_IDS = {
    "nes":       18,
    "snes":      19,
    "n64":        4,
    "gamecube":  21,
    "wii":       5,
    "wiiu":      41,
    "switch":   130,
    "gb":        33,
    "gbc":       22,
    "gba":       24,
    "nds":       20,
    "megadrive": 29,
    "dreamcast": 23,
    "ps1":        7,
    "ps2":        8,
    "ps3":        9,
    "psp":        38,
}

IGDB_API   = "https://api.igdb.com/v4"
TWITCH_URL = "https://id.twitch.tv/oauth2/token"
COVERS_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"


class IGDBError(Exception):
    pass


class IGDBClient:
    """
    Lichtgewicht IGDB-client zonder externe libraries.
    Gebruikt alleen de standaardbibliotheek (urllib).
    """

    def __init__(self, client_id: str, client_secret: str, cache_dir: str):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.cache_dir     = cache_dir
        self._token        = None
        self._token_expiry = 0
        self._token_path   = os.path.join(cache_dir, "igdb_token.json")
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cached_token()

    # ── Token beheer ───────────────────────────────────────────────────────────

    def _load_cached_token(self):
        if os.path.exists(self._token_path):
            try:
                with open(self._token_path, "r") as f:
                    data = json.load(f)
                if data.get("expiry", 0) > time.time() + 60:
                    self._token        = data["token"]
                    self._token_expiry = data["expiry"]
            except Exception:
                pass

    def _save_token(self):
        with open(self._token_path, "w") as f:
            json.dump({"token": self._token,
                       "expiry": self._token_expiry}, f)

    def _ensure_token(self):
        if self._token and time.time() < self._token_expiry - 60:
            return
        # Nieuw token ophalen
        params = urllib.parse.urlencode({
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "grant_type":    "client_credentials"
        }).encode()
        try:
            req = urllib.request.Request(TWITCH_URL, data=params, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            self._token        = data["access_token"]
            self._token_expiry = time.time() + data["expires_in"]
            self._save_token()
        except Exception as e:
            raise IGDBError(f"Token ophalen mislukt: {e}")

    # ── API requests ───────────────────────────────────────────────────────────

    def _post(self, endpoint: str, body: str) -> list:
        self._ensure_token()
        url = f"{IGDB_API}/{endpoint}"
        req = urllib.request.Request(
            url,
            data=body.encode(),
            headers={
                "Client-ID":     self.client_id,
                "Authorization": f"Bearer {self._token}",
                "Content-Type":  "text/plain",
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise IGDBError(f"IGDB HTTP {e.code}: {e.reason}")
        except Exception as e:
            raise IGDBError(f"IGDB request mislukt: {e}")

    # ── Publieke methodes ──────────────────────────────────────────────────────

    def search_games(self, name: str, console_id: str,
                     limit: int = 8) -> list[dict]:
        """
        Zoek games op naam, gefilterd op platform.
        Geeft een lijst van dicts terug:
          { id, name, cover_image_id, cover_url, summary, first_release_date }
        """
        platform = PLATFORM_IDS.get(console_id)
        platform_filter = f"& platforms = ({platform})" if platform else ""

        body = (
            f'search "{name}"; '
            f'fields name, cover.image_id, summary, first_release_date; '
            f'where version_parent = null {platform_filter}; '
            f'limit {limit};'
        )
        results = self._post("games", body)
        games = []
        for g in results:
            cover      = g.get("cover") or {}
            image_id   = cover.get("image_id", "")
            cover_url  = COVERS_URL.format(image_id=image_id) if image_id else ""
            year       = ""
            if g.get("first_release_date"):
                import datetime
                try:
                    year = str(datetime.datetime.fromtimestamp(
                        g["first_release_date"]).year)
                except Exception:
                    pass
            games.append({
                "igdb_id":      g["id"],
                "name":         g.get("name", ""),
                "cover_url":    cover_url,
                "image_id":     image_id,
                "summary":      g.get("summary", ""),
                "year":         year,
            })
        return games

    def download_cover(self, image_id: str, dest_path: str) -> bool:
        """
        Download een cover naar dest_path.
        Geeft True terug bij succes.
        """
        if not image_id:
            return False
        url = COVERS_URL.format(image_id=image_id)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            urllib.request.urlretrieve(url, dest_path)
            return True
        except Exception as e:
            print(f"[SCRAPER] Cover download mislukt: {e}")
            return False
