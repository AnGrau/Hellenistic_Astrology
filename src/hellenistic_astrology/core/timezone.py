from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

# Loi du 14 juin 1916 instaurant l'heure d'été en France : avant cette date,
# la résolution automatique via tzdata n'est pas considérée fiable.
MIN_RELIABLE_YEAR = 1916


@dataclass(frozen=True)
class BirthData:
    name: str
    latitude: float
    longitude: float
    local_date: date | None = None
    local_time: time | None = None
    tz_name: str | None = None
    utc_datetime: datetime | None = None


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
