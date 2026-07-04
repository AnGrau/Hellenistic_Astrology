"""Données de naissance (`BirthData`) et résolution en UTC. Fuseau résolu
automatiquement (place + heure locale via `zoneinfo`) à partir de 1916 ;
avant cette date, un `utc_datetime` explicite est obligatoire."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

# Loi du 14 juin 1916 instaurant l'heure d'été en France : avant cette date,
# la résolution automatique via tzdata n'est pas considérée fiable.
MIN_RELIABLE_YEAR = 1916


@dataclass(frozen=True)
class BirthData:
    name: str
    # latitude/longitude : coordonnées directes, toujours prioritaires si
    # fournies (aucun appel réseau). place : lieu en texte libre, résolu via
    # géocodage (core.geocoding) uniquement si latitude/longitude sont absents
    # — opt-in explicite, voir core/geocoding.py.
    latitude: float | None = None
    longitude: float | None = None
    place: str | None = None
    # Indice pays (ISO 3166-1 alpha-2, ex. "fr") pour restreindre la
    # recherche de géocodage et lever une ambiguïté (ex. plusieurs "Paris"
    # dans le monde). Ignoré si `place` n'est pas utilisé.
    country_code: str | None = None
    local_date: date | None = None
    local_time: time | None = None
    tz_name: str | None = None
    utc_datetime: datetime | None = None


def birth_data_from_dict(data: dict) -> BirthData:
    """Construit un BirthData depuis un dict JSON (name, latitude+longitude
    ou place [+ country_code optionnel], local_date/local_time/tz_name, ou
    utc_datetime en alternative)."""
    return BirthData(
        name=data["name"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        place=data.get("place"),
        country_code=data.get("country_code"),
        local_date=date.fromisoformat(data["local_date"]) if "local_date" in data else None,
        local_time=time.fromisoformat(data["local_time"]) if "local_time" in data else None,
        tz_name=data.get("tz_name"),
        utc_datetime=(
            datetime.fromisoformat(data["utc_datetime"]) if "utc_datetime" in data else None
        ),
    )


def resolve_utc(birth: BirthData) -> datetime:
    if birth.utc_datetime is not None:
        return birth.utc_datetime

    if birth.local_date is None or birth.local_time is None or birth.tz_name is None:
        raise ValueError(
            "Fournir soit utc_datetime, soit local_date + local_time + tz_name."
        )

    if birth.local_date.year < MIN_RELIABLE_YEAR:
        raise ValueError(
            f"Résolution automatique du fuseau non fiable avant {MIN_RELIABLE_YEAR} "
            f"(année {birth.local_date.year}) ; fournir utc_datetime explicitement."
        )

    local_dt = datetime.combine(
        birth.local_date, birth.local_time, tzinfo=ZoneInfo(birth.tz_name)
    )
    return local_dt.astimezone(timezone.utc)
