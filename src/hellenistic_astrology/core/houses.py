SIGNS = [
    "Bélier",
    "Taureau",
    "Gémeaux",
    "Cancer",
    "Lion",
    "Vierge",
    "Balance",
    "Scorpion",
    "Sagittaire",
    "Capricorne",
    "Verseau",
    "Poissons",
]


def sign_index(longitude: float) -> int:
    return int(longitude % 360 // 30)


def index_of_sign(name: str) -> int:
    return SIGNS.index(name)


def sign_name(longitude: float) -> str:
    return SIGNS[sign_index(longitude)]


def degree_in_sign(longitude: float) -> float:
    return longitude % 30


def longitude_of(sign: str, degree_in_sign: float) -> float:
    return index_of_sign(sign) * 30 + degree_in_sign


def whole_sign_house(longitude: float, ascendant_longitude: float) -> int:
    """Maison en signe entier : la maison 1 est le signe de l'Ascendant,
    chaque signe suivant compte pour une maison, quel que soit son degré."""
    return (sign_index(longitude) - sign_index(ascendant_longitude)) % 12 + 1
