"""
scraper/scraper_service.py
Verbindt IGDB-client met de RetroVault config.
Beheert het zoeken, previews tonen en opslaan van covers + metadata.
"""

import os
import threading
from scraper.igdb_client import IGDBClient, IGDBError


class ScrapeResult:
    """Resultaat van een zoekoperatie – gedeeld tussen thread en UI."""
    def __init__(self):
        self.results:  list  = []
        self.error:    str   = ""
        self.loading:  bool  = False
        self.done:     bool  = False


class ScraperService:
    """
    Hoge-niveau scraper interface voor de UI.
    Alle netwerkoperaties draaien in een achtergrondthread
    zodat de UI niet blokkeert.
    """

    def __init__(self, config_manager):
        self.cfg     = config_manager
        self._client = None
        self._init_client()

    def _init_client(self):
        cid    = self.cfg.settings.get("igdb_client_id", "")
        secret = self.cfg.settings.get("igdb_client_secret", "")
        if cid and secret:
            cache_dir    = os.path.join(self.cfg.base_dir, "config", "cache")
            self._client = IGDBClient(cid, secret, cache_dir)

    def is_configured(self) -> bool:
        return self._client is not None

    def reload_credentials(self):
        """Herlaad na het opslaan van nieuwe credentials in settings."""
        self._client = None
        self._init_client()

    def search_async(self, game_name: str, console_id: str) -> ScrapeResult:
        """
        Start een achtergrondzoektocht. Geeft meteen een ScrapeResult terug.
        De UI pollt result.done om te weten wanneer het klaar is.
        """
        result         = ScrapeResult()
        result.loading = True

        def _run():
            try:
                result.results = self._client.search_games(game_name, console_id)
            except IGDBError as e:
                result.error = str(e)
            except Exception as e:
                result.error = f"Onverwachte fout: {e}"
            finally:
                result.loading = False
                result.done    = True

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return result

    def save_cover(self, console: dict, game: dict,
                   image_id: str, igdb_name: str = None) -> bool:
        """
        Download de cover en sla op in assets/covers/<console_id>/<game_id>.jpg.
        Updatet game["cover"] en schrijft consoles.json weg.
        Optioneel: overschrijf de gamenaam met de IGDB-naam.
        """
        if not self._client:
            return False

        console_id = console["id"]
        game_id    = game["id"]
        dest_dir   = os.path.join(self.cfg.base_dir, "assets", "covers", console_id)
        dest_path  = os.path.join(dest_dir, f"{game_id}.jpg")

        ok = self._client.download_cover(image_id, dest_path)
        if not ok:
            return False

        # Relatief pad opslaan
        rel = os.path.relpath(dest_path, self.cfg.base_dir).replace("\\", "/")
        game["cover"] = rel
        if igdb_name:
            game["name"] = igdb_name

        # Sync naar cfg.consoles
        for c in self.cfg.consoles:
            if c["id"] == console_id:
                for g in c.get("games", []):
                    if g["id"] == game_id:
                        g["cover"] = rel
                        if igdb_name:
                            g["name"] = igdb_name
                        break

        self.cfg.save_consoles()
        return True

    def save_cover_async(self, console: dict, game: dict,
                         image_id: str, igdb_name: str = None) -> ScrapeResult:
        """Zelfde als save_cover maar asynchroon (download kan even duren)."""
        result         = ScrapeResult()
        result.loading = True

        def _run():
            ok = self.save_cover(console, game, image_id, igdb_name)
            result.error   = "" if ok else "Download mislukt"
            result.loading = False
            result.done    = True

        threading.Thread(target=_run, daemon=True).start()
        return result
