from dataclasses import dataclass
from datetime import datetime, timedelta

from .dignities import DOMICILES
from .houses import SIGNS, index_of_sign

# Années fixes de la libération zodiacale (Vettius Valens, Anthologiae),
# vérifiées par recoupement de 3 sources indépendantes et cohérentes entre
# elles : transcription du podcast de Chris Brennan (épisode 192, citant
# directement Valens), calculateur Augurine, synthèse kerykeion. Capricorne
# (27 ans) diffère volontairement d'Aquarius (30 ans) bien que les deux
# soient domicile de Saturne — particularité documentée de la technique,
# pas une erreur de recopie (aucune fixture Anthony/Liam ne couvre ce calcul,
# voir CLAUDE.md).
ZODIACAL_RELEASING_YEARS: dict[str, int] = {
    "Bélier": 15,
    "Taureau": 8,
    "Gémeaux": 20,
    "Cancer": 25,
    "Lion": 19,
    "Vierge": 20,
    "Balance": 8,
    "Scorpion": 15,
    "Sagittaire": 12,
    "Capricorne": 27,
    "Verseau": 30,
    "Poissons": 12,
}

SIGN_RULERS: dict[str, str] = {sign: planet for planet, signs in DOMICILES.items() for sign in signs}

# La technique utilise une année "égyptienne" de 360 jours (12 mois de 30
# jours) et non l'année solaire de 365,25 jours — confirmé explicitement par
# Chris Brennan (même transcription que ci-dessus) : les dates réelles
# calculées "dérivent" donc légèrement par rapport au calendrier solaire au
# fil des décennies, c'est un effet attendu de la technique, pas un bug.
# Chaque niveau divise l'unité du niveau parent par 12 (année → mois → "jour"
# de 2,5 jours → "heure" de 5 heures), d'où la structure auto-similaire.
DAYS_PER_YEAR = 360.0
DAYS_PER_LEVEL: tuple[float, ...] = (
    DAYS_PER_YEAR,
    DAYS_PER_YEAR / 12,
    DAYS_PER_YEAR / 144,
    DAYS_PER_YEAR / 1728,
)

MAX_LEVEL = 4


@dataclass(frozen=True)
class ReleasingPeriod:
    level: int  # 1 (périodes générales) à 4
    sign: str
    ruler: str
    start: datetime
    end: datetime


def _next_sign(sign: str) -> str:
    return SIGNS[(index_of_sign(sign) + 1) % 12]


def level_periods(level: int, start_sign: str, start: datetime, duration: timedelta) -> list[ReleasingPeriod]:
    """Découpe `duration` à partir de `start` en périodes consécutives de
    signes de `level`, à partir de `start_sign`, tournant autant de fois que
    nécessaire autour du zodiaque (cas fréquent : la durée d'un signe au
    niveau parent dépasse presque toujours la somme d'un tour complet des 12
    signes à l'unité du niveau courant). La dernière période est tronquée
    pour s'arrêter exactement à `start + duration`.
    """
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"level doit être entre 1 et {MAX_LEVEL} : {level}")

    days_per_unit = DAYS_PER_LEVEL[level - 1]
    end = start + duration
    periods = []
    sign = start_sign
    cursor = start
    while cursor < end:
        length = timedelta(days=ZODIACAL_RELEASING_YEARS[sign] * days_per_unit)
        period_end = min(cursor + length, end)
        periods.append(
            ReleasingPeriod(level=level, sign=sign, ruler=SIGN_RULERS[sign], start=cursor, end=period_end)
        )
        cursor = period_end
        sign = _next_sign(sign)
    return periods


def sub_periods(parent: ReleasingPeriod) -> list[ReleasingPeriod]:
    """Périodes du niveau directement inférieur, à l'intérieur de `parent`.

    Toujours démarrées sur le même signe que `parent` (règle explicite de
    Valens/Brennan : "the first level two within that level one will always
    be the same sign") et bornées exactement à la durée réelle de `parent`.
    """
    if parent.level >= MAX_LEVEL:
        raise ValueError(f"Pas de niveau au-delà de {MAX_LEVEL}.")
    return level_periods(parent.level + 1, parent.sign, parent.start, parent.end - parent.start)


def releasing_tree(
    lot_sign: str, birth: datetime, horizon: datetime, max_level: int = MAX_LEVEL
) -> list[ReleasingPeriod]:
    """Calcule récursivement les niveaux 1 à `max_level` de la libération
    zodiacale à partir du signe de la Part (Fortune ou Esprit), de `birth`
    jusqu'à `horizon`. Retourne une liste plate de toutes les périodes de
    tous les niveaux calculés (chaque période porte son propre `level`,
    `start`/`end` permettent de reconstituer la hiérarchie parent/enfant).

    Contrairement aux niveaux 2 à 4 (bornés exactement par la durée réelle de
    leur période parente), le niveau 1 est tronqué à `horizon` par simple
    commodité pratique (limite arbitraire de calcul) : passer un `horizon`
    largement au-delà de l'âge qui intéresse l'appelant pour obtenir des
    périodes de niveau 1 non tronquées en pratique.
    """
    if not 1 <= max_level <= MAX_LEVEL:
        raise ValueError(f"max_level doit être entre 1 et {MAX_LEVEL} : {max_level}")

    periods = level_periods(1, lot_sign, birth, horizon - birth)
    for level in range(2, max_level + 1):
        parents = [p for p in periods if p.level == level - 1]
        for parent in parents:
            periods.extend(sub_periods(parent))
    return periods


def active_period(periods: list[ReleasingPeriod], level: int, when: datetime) -> ReleasingPeriod | None:
    """Période de `level` active à la date `when`, ou None si `when` est hors
    de la plage couverte par `periods` (avant le début ou après l'horizon)."""
    for period in periods:
        if period.level == level and period.start <= when < period.end:
            return period
    return None
