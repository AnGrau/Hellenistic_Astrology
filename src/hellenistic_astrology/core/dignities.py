from dataclasses import dataclass

from .houses import SIGNS, whole_sign_house

# Domiciles traditionnels (avant l'attribution des planètes modernes).
DOMICILES: dict[str, tuple[str, ...]] = {
    "Soleil": ("Lion",),
    "Lune": ("Cancer",),
    "Mercure": ("Gémeaux", "Vierge"),
    "Vénus": ("Taureau", "Balance"),
    "Mars": ("Bélier", "Scorpion"),
    "Jupiter": ("Sagittaire", "Poissons"),
    "Saturne": ("Capricorne", "Verseau"),
}

EXALTATIONS: dict[str, str] = {
    "Soleil": "Bélier",
    "Lune": "Taureau",
    "Mercure": "Vierge",
    "Vénus": "Poissons",
    "Mars": "Capricorne",
    "Jupiter": "Cancer",
    "Saturne": "Balance",
}

# Accord grammatical du mot "pérégrin(e)" selon le genre du nom de la planète.
FEMININE_PLANETS = {"Lune", "Vénus"}


def opposite_sign(sign: str) -> str:
    return SIGNS[(sign_index_of_name(sign) + 6) % 12]


def sign_index_of_name(sign: str) -> int:
    return SIGNS.index(sign)


def essential_dignity(planet: str, sign: str) -> str:
    domiciles = DOMICILES.get(planet, ())
    if sign in domiciles:
        return "Domicile"

    exaltation = EXALTATIONS.get(planet)
    if sign == exaltation:
        return "Exaltation"

    detriments = {opposite_sign(s) for s in domiciles}
    if sign in detriments:
        return "Exil (détriment)"

    if exaltation and sign == opposite_sign(exaltation):
        return "Chute"

    return "Pérégrine" if planet in FEMININE_PLANETS else "Pérégrin"


@dataclass(frozen=True)
class Rulership:
    planet: str
    domicile_signs: tuple[str, ...]
    houses_governed: tuple[int, ...]


def traditional_rulerships(ascendant_longitude: float) -> list[Rulership]:
    """Table des maîtrises : pour chaque planète classique, ses domiciles et
    les maisons (en signe entier) qu'elle gouverne depuis l'Ascendant."""
    rulerships = []
    for planet, domicile_signs in DOMICILES.items():
        ordered_signs = tuple(sorted(domicile_signs, key=sign_index_of_name))
        houses = tuple(
            whole_sign_house(sign_index_of_name(sign) * 30, ascendant_longitude)
            for sign in ordered_signs
        )
        rulerships.append(Rulership(planet=planet, domicile_signs=ordered_signs, houses_governed=houses))
    return rulerships
