from dataclasses import dataclass

from .houses import SIGNS, index_of_sign, whole_sign_house

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
    return SIGNS[(index_of_sign(sign) + 6) % 12]


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
        ordered_signs = tuple(sorted(domicile_signs, key=index_of_sign))
        houses = tuple(
            whole_sign_house(index_of_sign(sign) * 30, ascendant_longitude)
            for sign in ordered_signs
        )
        rulerships.append(Rulership(planet=planet, domicile_signs=ordered_signs, houses_governed=houses))
    return rulerships


@dataclass(frozen=True)
class MutualReception:
    planet_a: str
    planet_b: str


def mutual_receptions_by_domicile(positions: dict[str, str]) -> list[MutualReception]:
    """Réceptions mutuelles par domicile entre planètes classiques : A est
    dans un domicile de B, et B est dans un domicile de A, simultanément.

    `positions` associe chaque planète à son signe ; l'ordre d'itération du
    dict détermine l'ordre (planet_a, planet_b) de chaque paire détectée.
    """
    names = list(positions.keys())
    receptions = []
    for i, planet_a in enumerate(names):
        for planet_b in names[i + 1 :]:
            if positions[planet_a] in DOMICILES.get(planet_b, ()) and positions[
                planet_b
            ] in DOMICILES.get(planet_a, ()):
                receptions.append(MutualReception(planet_a=planet_a, planet_b=planet_b))
    return receptions
