"""Résolution d'un lieu en texte libre vers des coordonnées (opt-in).

Seul module de core/ qui effectue un appel réseau : il envoie le texte du
lieu à Nominatim (OpenStreetMap), un service tiers. N'est jamais appelé si
des coordonnées latitude/longitude sont déjà fournies (voir
resolve_coordinates ci-dessous) — la saisie directe de lat/lon reste le
chemin par défaut et n'envoie aucune donnée sur le réseau.
"""

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .timezone import BirthData

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "hellenistic-astrology-cli (https://github.com/AnGrau/Hellenistic_Astrology)"
DEFAULT_TIMEOUT = 10.0
# Nombre de résultats demandés à Nominatim : au-delà de 1, ça permet de
# détecter une ambiguïté (plusieurs lieux distincts) plutôt que de deviner
# silencieusement en ne regardant que le premier résultat.
CANDIDATE_LIMIT = 5
# Deux résultats à moins de cette distance sont considérés comme le même
# lieu (Nominatim renvoie parfois plusieurs entités OSM distinctes — ville
# et département, par ex. — pour un même lieu réel). Négligeable pour un
# thème natal : quelques km ne changent pas les maisons/aspects.
SAME_PLACE_THRESHOLD_KM = 5.0


class GeocodingError(Exception):
    pass


def _approx_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance approximative (projection équirectangulaire) : largement
    suffisante à cette échelle, pas besoin de la précision d'une Haversine."""
    lat_avg_rad = math.radians((lat1 + lat2) / 2)
    dx = (lon2 - lon1) * 111.32 * math.cos(lat_avg_rad)
    dy = (lat2 - lat1) * 110.57
    return math.hypot(dx, dy)


def _distinct_locations(results: list[dict]) -> list[dict]:
    """Regroupe les résultats par proximité géographique : un représentant
    par lieu réellement distinct (le premier résultat rencontré du groupe,
    déjà le mieux classé par Nominatim)."""
    distinct: list[dict] = []
    for result in results:
        lat, lon = float(result["lat"]), float(result["lon"])
        if not any(
            _approx_distance_km(lat, lon, float(d["lat"]), float(d["lon"]))
            <= SAME_PLACE_THRESHOLD_KM
            for d in distinct
        ):
            distinct.append(result)
    return distinct


@dataclass(frozen=True)
class GeocodingResult:
    latitude: float
    longitude: float
    display_name: str


def geocode(
    place: str, country_code: str | None = None, timeout: float = DEFAULT_TIMEOUT
) -> GeocodingResult:
    """Résout `place` en coordonnées via l'API de recherche Nominatim.

    Lève GeocodingError si aucun résultat, ou si plusieurs résultats
    distincts sont trouvés (ambiguïté, ex. plusieurs "Paris" dans le monde)
    plutôt que de deviner silencieusement en prenant le premier. `country_code`
    (ISO 3166-1 alpha-2, ex. "fr") restreint la recherche côté Nominatim pour
    lever l'ambiguïté en amont.
    """
    params = {"q": place, "format": "json", "limit": CANDIDATE_LIMIT}
    if country_code:
        params["countrycodes"] = country_code
    query = urllib.parse.urlencode(params)
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

    distinct = _distinct_locations(results)
    if len(distinct) > 1:
        candidates = "\n".join(f"  - {r.get('display_name', '?')}" for r in distinct)
        raise GeocodingError(
            f"Le lieu « {place} » est ambigu ({len(distinct)} lieux distincts trouvés). "
            "Précisez `place` (ex. ajouter le pays/la région) ou ajoutez `country_code` :\n"
            f"{candidates}"
        )

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
        result = geocode(birth.place, country_code=birth.country_code)
        return result.latitude, result.longitude

    raise ValueError("Fournir soit latitude + longitude, soit place.")
