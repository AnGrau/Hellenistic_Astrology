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


@dataclass(frozen=True)
class SolarProximity:
    planet: str
    gap_degrees: float


def solar_proximity(sun_longitude: float, planet_longitudes: dict[str, float]) -> list[SolarProximity]:
    """Écart angulaire réel (`aspects.angular_gap`) entre chaque planète et
    le Soleil — pas de seuil ici : la classification « combuste » (< 15°,
    seuil « sous les rayons » confirmé par les deux thèmes de référence, déjà
    promis en Phase 1 par CLAUDE.md) est une décision de rendu, prise dans
    docgen (cohérent avec `direction_label`/`format_dms`, déjà des fonctions
    de classification côté docgen sur des données brutes)."""
    # Import tardif : évite le cycle dignities -> aspects -> observation ->
    # dignities (aspects importe PointPosition depuis observation, qui
    # importe MutualReception/SolarProximity d'ici).
    from .aspects import angular_gap

    return [
        SolarProximity(planet=name, gap_degrees=angular_gap(sun_longitude, longitude))
        for name, longitude in planet_longitudes.items()
    ]


# Maîtres de triplicité, système dorothéen/hellénistique (Dorothée de Sidon,
# tel que documenté par Chris Brennan) — distinct du système ptoléméen
# simplifié, qui unifie le maître Eau jour/nuit sur Mars sans maître
# participant. Vérifié contre deux sources indépendantes (Wikipedia "Triplicity"
# et Augurine, cohérentes entre elles) faute de fixture de référence pour ce
# calcul : ni le thème d'Anthony ni celui de Liam ne documentent la triplicité.
TRIPLICITY_RULERS: dict[str, dict[str, str]] = {
    "Feu": {"jour": "Soleil", "nuit": "Jupiter", "participant": "Saturne"},
    "Terre": {"jour": "Vénus", "nuit": "Lune", "participant": "Mars"},
    "Air": {"jour": "Saturne", "nuit": "Mercure", "participant": "Jupiter"},
    "Eau": {"jour": "Vénus", "nuit": "Mars", "participant": "Lune"},
}

SIGN_TRIPLICITY: dict[str, str] = {
    "Bélier": "Feu",
    "Lion": "Feu",
    "Sagittaire": "Feu",
    "Taureau": "Terre",
    "Vierge": "Terre",
    "Capricorne": "Terre",
    "Gémeaux": "Air",
    "Balance": "Air",
    "Verseau": "Air",
    "Cancer": "Eau",
    "Scorpion": "Eau",
    "Poissons": "Eau",
}


def triplicity_dignity(planet: str, sign: str) -> str | None:
    """Maîtrise de triplicité de `planet` dans `sign`, si applicable.

    Les trois maîtres (jour/nuit/participant) sont tous considérés comme
    dignifiés par triplicité — la secte de la carte détermine lequel est
    prioritaire pour l'interprétation (hors périmètre ici), pas l'éligibilité
    elle-même. Un signe n'a jamais deux fois la même planète parmi ses trois
    maîtres, donc au plus une des trois conditions ci-dessous peut être vraie.
    """
    rulers = TRIPLICITY_RULERS[SIGN_TRIPLICITY[sign]]
    if planet == rulers["jour"]:
        return "Maître de triplicité (jour)"
    if planet == rulers["nuit"]:
        return "Maître de triplicité (nuit)"
    if planet == rulers["participant"]:
        return "Maître de triplicité (participant)"
    return None


# Bornes/termes égyptiens : chaque signe est divisé en 5 segments inégaux,
# chacun attribué à l'une des 5 planètes non-luminaires. Table transmise par
# Vettius Valens (Anthologiae, Livre I) et reprise par Chris Brennan
# (Hellenistic Astrology). Fournie et vérifiée par l'utilisateur — voir
# docs/table_termes_egyptiens.md pour les sources et la méthode de vérification
# (aucune fixture Anthony/Liam ne documente les bornes).
# Chaque valeur : liste de (borne supérieure exclusive, planète), les bornes
# étant cumulatives à partir de 0° et totalisant 30° par signe.
EGYPTIAN_BOUNDS: dict[str, list[tuple[float, str]]] = {
    "Bélier": [(6, "Jupiter"), (12, "Vénus"), (20, "Mercure"), (25, "Mars"), (30, "Saturne")],
    "Taureau": [(8, "Vénus"), (14, "Mercure"), (22, "Jupiter"), (27, "Saturne"), (30, "Mars")],
    "Gémeaux": [(6, "Mercure"), (12, "Jupiter"), (17, "Vénus"), (24, "Mars"), (30, "Saturne")],
    "Cancer": [(7, "Mars"), (13, "Vénus"), (19, "Mercure"), (26, "Jupiter"), (30, "Saturne")],
    "Lion": [(6, "Jupiter"), (11, "Vénus"), (18, "Saturne"), (24, "Mercure"), (30, "Mars")],
    "Vierge": [(7, "Mercure"), (13, "Vénus"), (18, "Jupiter"), (24, "Saturne"), (30, "Mars")],
    "Balance": [(6, "Saturne"), (14, "Mercure"), (21, "Jupiter"), (28, "Vénus"), (30, "Mars")],
    "Scorpion": [(7, "Mars"), (11, "Vénus"), (19, "Mercure"), (24, "Jupiter"), (30, "Saturne")],
    "Sagittaire": [(12, "Jupiter"), (17, "Vénus"), (21, "Mercure"), (26, "Saturne"), (30, "Mars")],
    "Capricorne": [(7, "Mercure"), (14, "Jupiter"), (22, "Vénus"), (26, "Saturne"), (30, "Mars")],
    "Verseau": [(7, "Mercure"), (13, "Vénus"), (20, "Jupiter"), (25, "Mars"), (30, "Saturne")],
    "Poissons": [(12, "Vénus"), (16, "Jupiter"), (19, "Mercure"), (28, "Mars"), (30, "Saturne")],
}


def egyptian_bound_ruler(sign: str, degree_in_sign: float) -> str:
    """Maître du terme (bornes égyptiennes) occupé par ce degré, indépendamment
    de la planète qui s'y trouve."""
    if not (0 <= degree_in_sign < 30):
        raise ValueError(f"degree_in_sign doit être dans [0, 30) : {degree_in_sign}")
    for upper_bound, ruler in EGYPTIAN_BOUNDS[sign]:
        if degree_in_sign < upper_bound:
            return ruler
    raise AssertionError(f"Table de bornes incomplète pour {sign} — devrait couvrir [0, 30).")


def bound_dignity(planet: str, sign: str, degree_in_sign: float) -> str | None:
    """"Maître du terme" si `planet` est elle-même la maîtresse du terme
    (borne égyptienne) qu'elle occupe, sinon None."""
    if planet == egyptian_bound_ruler(sign, degree_in_sign):
        return "Maître du terme (bornes égyptiennes)"
    return None


# Décans (faces) : chaque signe est divisé en 3 segments égaux de 10°,
# maîtres selon l'ordre chaldéen — qui cycle en continu à travers les 36
# décans du zodiaque, sans se réinitialiser à chaque signe. Bélier 1er décan
# = Mars (tel qu'utilisé par Vettius Valens et Hephaistion). Vérifié contre
# deux sources indépendantes et cohérentes entre elles (synthèse citant
# Valens/Hephaistion, table complète des 36 décans d'Augurine) — aucune
# fixture Anthony/Liam ne documente les décans non plus.
CHALDEAN_ORDER: tuple[str, ...] = ("Saturne", "Jupiter", "Mars", "Soleil", "Vénus", "Mercure", "Lune")

# Position de Mars (maître du 1er décan du Bélier) dans CHALDEAN_ORDER.
_ARIES_FIRST_DECAN_OFFSET = CHALDEAN_ORDER.index("Mars")


def decan_ruler(sign: str, degree_in_sign: float) -> str:
    """Maître du décan (face) occupé par ce degré dans ce signe."""
    if not (0 <= degree_in_sign < 30):
        raise ValueError(f"degree_in_sign doit être dans [0, 30) : {degree_in_sign}")
    decan_within_sign = int(degree_in_sign // 10)  # 0, 1 ou 2
    global_decan_index = index_of_sign(sign) * 3 + decan_within_sign
    return CHALDEAN_ORDER[(global_decan_index + _ARIES_FIRST_DECAN_OFFSET) % 7]


def decan_dignity(planet: str, sign: str, degree_in_sign: float) -> str | None:
    """"Maître du décan" si `planet` est elle-même la maîtresse du décan
    (face) qu'elle occupe, sinon None."""
    if planet == decan_ruler(sign, degree_in_sign):
        return "Maître du décan"
    return None
