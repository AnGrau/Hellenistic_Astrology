"""Résolution d'un lieu en texte libre vers des coordonnées (opt-in).

Seul module de core/ qui effectue un appel réseau : il envoie le texte du
lieu à Nominatim (OpenStreetMap), un service tiers. N'est jamais appelé si
des coordonnées latitude/longitude sont déjà fournies (voir
resolve_coordinates ci-dessous) — la saisie directe de lat/lon reste le
chemin par défaut et n'envoie aucune donnée sur le réseau.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .timezone import BirthData

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "hellenistic-astrology-cli (https://github.com/AnGrau/Hellenistic_Astrology)"
DEFAULT_TIMEOUT = 10.0


class GeocodingError(Exception):
    pass


@dataclass(frozen=True)
class GeocodingResult:
    latitude: float
    longitude: float
    display_name: str


def geocode(place: str, timeout: float = DEFAULT_TIMEOUT) -> GeocodingResult:
    """Résout `place` en coordonnées via l'API de recherche Nominatim."""
    query = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1})
    request = urllib.request.Request(
        f"{NOMINATIM_URL}?{query}", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            results = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GeocodingError(f"Échec de la résolution du lieu « {place} » : {exc}") from exc

    if not results:
        raise GeocodingError(f"Aucun résultat pour le lieu « {place} ».")

    result = results[0]
    return GeocodingResult(
        latitude=float(result["lat"]),
        longitude=float(result["lon"]),
        display_name=result.get("display_name", place),
    )


def resolve_coordinates(birth: BirthData) -> tuple[float, float]:
    """Renvoie (latitude, longitude) pour un BirthData.

    Priorité aux coordonnées directes (aucun appel réseau). Si elles sont
    absentes et qu'un `place` est fourni, résout via geocode() — c'est le
    seul cas qui déclenche un appel réseau.
    """
    if birth.latitude is not None and birth.longitude is not None:
        return birth.latitude, birth.longitude

    if birth.place:
        result = geocode(birth.place)
        return result.latitude, result.longitude

    raise ValueError("Fournir soit latitude + longitude, soit place.")
