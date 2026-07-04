"""Interface avec le Swiss Ephemeris (`pyswisseph`) : positions planétaires,
Ascendant/Milieu du Ciel, Nœud Nord. Bascule automatiquement sur la théorie
Moshier/Moseph (précision ~1 arcseconde) si les fichiers `.se1` de
`data/ephe/` (voir `scripts/fetch_ephemeris.py`) sont absents.
"""

import os
from dataclasses import dataclass
from datetime import datetime

import swisseph as swe

# Planètes classiques utilisées en astrologie hellénistique (pas de planètes
# modernes : Uranus, Neptune, Pluton sont hors périmètre).
CLASSICAL_PLANETS: dict[str, int] = {
    "Soleil": swe.SUN,
    "Lune": swe.MOON,
    "Mercure": swe.MERCURY,
    "Vénus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturne": swe.SATURN,
}


@dataclass(frozen=True)
class RawPosition:
    longitude: float
    speed: float

    @property
    def retrograde(self) -> bool:
        return self.speed < 0


def julian_day_utc(dt_utc: datetime) -> float:
    hour = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def compute_flags(ephe_path: str) -> int:
    """Utilise le Swiss Ephemeris si les fichiers .se1 sont présents, sinon
    bascule sur la théorie Moshier/Moseph (précision ~1 arcseconde, sans fichiers)."""
    has_files = os.path.isdir(ephe_path) and any(
        f.endswith(".se1") for f in os.listdir(ephe_path)
    )
    base = swe.FLG_SWIEPH if has_files else swe.FLG_MOSEPH
    return base | swe.FLG_SPEED


def set_ephemeris_path(ephe_path: str) -> None:
    swe.set_ephe_path(ephe_path)


def planet_positions(jd_ut: float, flags: int) -> dict[str, RawPosition]:
    positions = {}
    for name, code in CLASSICAL_PLANETS.items():
        xx, _retflag = swe.calc_ut(jd_ut, code, flags)
        positions[name] = RawPosition(longitude=xx[0], speed=xx[3])
    return positions


def north_node(jd_ut: float, flags: int) -> RawPosition:
    """Nœud Nord vrai (TRUE_NODE, pas MEAN_NODE) : le nœud moyen avance de
    façon monotone et ne station jamais, alors que les deux thèmes de
    référence montrent des directions "Direct (rare)" / "Rétrograde
    (usuel)" caractéristiques du nœud vrai, qui oscille et statione."""
    xx, _retflag = swe.calc_ut(jd_ut, swe.TRUE_NODE, flags)
    return RawPosition(longitude=xx[0], speed=xx[3])


def ascendant_midheaven(jd_ut: float, latitude: float, longitude: float) -> tuple[float, float]:
    """Renvoie (ascendant, milieu du ciel) en longitude écliptique.

    Le système de maison passé à swe.houses n'affecte pas ces deux angles ;
    on utilise Placidus par défaut, les maisons en signes entiers sont
    recalculées nous-mêmes dans core.houses.
    """
    _cusps, ascmc = swe.houses(jd_ut, latitude, longitude, b"P")
    return ascmc[0], ascmc[1]
