"""Télécharge les fichiers de données Swiss Ephemeris nécessaires aux calculs.

Sans ces fichiers, le module core.ephemeris bascule automatiquement sur la
théorie Moshier (précision ~1 arcseconde, suffisante pour les tests de
régression mais pas pour une précision de niveau Astro.com sur toute
l'histoire du calendrier).

Avant un usage en production, vérifier les conditions de redistribution
exactes sur https://www.astro.com/swisseph/swisseph.htm — ce script se
contente de télécharger les fichiers dans data/ephe/ (gitignored), il ne les
committe pas.
"""

import urllib.request
from pathlib import Path

BASE_URL = "https://www.astro.com/ftp/swisseph/ephe/"
# Couvrent 1800-2399 : largement suffisant pour les thèmes natals traités ici.
FILES = ["sepl_18.se1", "semo_18.se1"]

TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "ephe"


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for filename in FILES:
        target = TARGET_DIR / filename
        if target.exists():
            print(f"déjà présent : {target}")
            continue
        url = BASE_URL + filename
        print(f"téléchargement {url} -> {target}")
        urllib.request.urlretrieve(url, target)


if __name__ == "__main__":
    main()
