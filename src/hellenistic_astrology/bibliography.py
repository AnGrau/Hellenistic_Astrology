"""Vérification des URLs bibliographiques citées dans CLAUDE.md.

CLAUDE.md demande de revérifier ces URLs avant chaque publication plutôt
que de les recopier sans contrôle. Garder REFERENCES synchronisée avec la
section "Références bibliographiques de travail" de CLAUDE.md — un test
(tests/test_bibliography.py) vérifie que les deux listes d'URLs coïncident.
"""

import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "hellenistic-astrology-cli (https://github.com/AnGrau/Hellenistic_Astrology)"
DEFAULT_TIMEOUT = 10.0

REFERENCES: list[tuple[str, str]] = [
    (
        "Chris Brennan, Hellenistic Astrology: The Study of Fate and Fortune",
        "https://theastrologypodcast.com/books/",
    ),
    (
        "Demetra George, Ancient Astrology in Theory and Practice, Volume I",
        "https://rubedo.press/ancient-astrology",
    ),
    (
        "Demetra George, Ancient Astrology in Theory and Practice, Volume II",
        "https://rubedo.press/ancient-astrology-volume-two",
    ),
    (
        "Demetra George, Astrology for Yourself / Astrology and the Authentic Self",
        "https://demetra-george.com/books/",
    ),
]


@dataclass(frozen=True)
class ReferenceCheck:
    label: str
    url: str
    ok: bool
    detail: str


def _check_url(url: str, timeout: float = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    """Vérifie une URL en HEAD, avec repli en GET si le serveur ne supporte
    pas HEAD (405/501) ou renvoie un statut inattendu."""
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
            if 200 <= status < 400:
                return True, f"{method} {status}"
            if method == "HEAD":
                continue
            return False, f"{method} {status}"
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (405, 501):
                continue
            return False, f"{method} erreur HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return False, f"{method} échec réseau : {exc}"
    return False, "échec (HEAD et GET)"


def check_all(timeout: float = DEFAULT_TIMEOUT) -> list[ReferenceCheck]:
    results = []
    for label, url in REFERENCES:
        ok, detail = _check_url(url, timeout=timeout)
        results.append(ReferenceCheck(label=label, url=url, ok=ok, detail=detail))
    return results
