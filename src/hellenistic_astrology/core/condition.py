"""Grille de condition planétaire (jalon 44) : bonification/corruption par
aspect, enclosure (besiegement) par signe, phénomènes solaires imbriqués
(cazimi/combustion/sous les rayons), et classement à 6 niveaux des 7
planètes classiques — Demetra George, *Ancient Astrology in Theory and
Practice, Vol. I : Assessing Planetary Condition* (titre repris pour ce
module) ; Chris Brennan, *Hellenistic Astrology*.

Module distinct de `dignities.py` (entièrement basé sur le signe/la
position d'un seul point à la fois) : tout ici est **relationnel**,
nécessite de connaître simultanément la position des 7 planètes —
architecturalement plus proche d'`aspects.py`.

Aucune fixture Anthony/Liam ne documente cette grille (comme la
triplicité/les bornes/les décans en leur temps) : règles vérifiées contre
les sources ci-dessus, tests synthétiques uniquement. Plusieurs ordinaux
de classement (secte, dignité) sont des jugements documentés, pas des
faits sourcés au même degré que les règles de bonification/corruption/
enclosure elles-mêmes — voir le plan du jalon 44 pour le détail.

Le **phasis** (proximité d'une station ou d'un lever/coucher héliaque)
est explicitement hors périmètre ici, différé à un jalon séparé."""

from dataclasses import dataclass, replace

from .aspects import is_applying, sign_aspect
from .dignities import MutualReception, SolarProximity
from .ephemeris import CLASSICAL_PLANETS
from .houses import SIGNS, index_of_sign, longitude_of
from .observation import PointPosition
from .sect import BENEFICS, MALEFICS

# Seuils des phénomènes solaires imbriqués. `UNDER_RAYS_ORB_DEGREES` a la
# même valeur que `docgen.builder.COMBUSTION_ORB_DEGREES` (jalon 20, déjà
# validé mot pour mot contre Anthony/Liam) — dupliquée volontairement ici,
# jamais importée : `core/` ne doit jamais dépendre de `docgen/`. Ce module
# ajoute deux paliers plus fins (cazimi, combustion) à l'intérieur de ce
# seuil déjà validé, il ne le remplace pas. 9° (pas "8-9°") : nombre précis
# de la convention hellénistique citée (Demetra George), par opposition aux
# 12°/17' de la convention médiévale plus tardive.
CAZIMI_ORB_DEGREES = 1.0
TRUE_COMBUSTION_ORB_DEGREES = 9.0
UNDER_RAYS_ORB_DEGREES = 15.0

# Seuil d'enclosure par signe (jalon 44). Mesuré depuis la frontière de
# CHAQUE planète encadrante avec le signe de la planète encadrée — pas
# depuis le degré exact de la planète encadrée elle-même. Cette dernière
# lecture, plus littérale par rapport à la citation source, a été
# envisagée puis abandonnée : elle rend l'enclosure des deux côtés
# géométriquement impossible simultanément (avec un seuil de 7° sur un
# signe de 30°, un point ne peut jamais être à moins de 7° de ses deux
# propres frontières de signe à la fois — 7+7=14 < 30). Découvert en
# écrivant les tests, corrigé après validation explicite avec
# l'utilisateur : chaque planète encadrante doit être dans les 7 derniers
# (côté précédent) ou 7 premiers (côté suivant) degrés de SON PROPRE signe,
# indépendamment du degré exact de la planète encadrée.
ENCLOSURE_ORB_DEGREES = 7.0


@dataclass(frozen=True)
class AspectInfluence:
    source: str  # planète en cause (Vénus/Jupiter/Mars/Saturne)
    aspect: str  # "Conjonction" | "Sextile" | "Carré" | "Trigone" | "Opposition"


@dataclass(frozen=True)
class BonificationCorruption:
    planet: str
    aided_by: tuple[AspectInfluence, ...] = ()
    harmed_by: tuple[AspectInfluence, ...] = ()


@dataclass(frozen=True)
class Enclosure:
    planet: str
    # Les deux planètes encadrantes si les deux côtés sont occupés à moins
    # de 7°, quelle que soit leur nature (transparence) — `category`
    # ci-dessous est None si la nature est mixte, mais `flanking_planets`
    # reste renseigné (choix non sourcé, à revoir si besoin).
    flanking_planets: tuple[str, str] | None = None
    category: str | None = None  # "bénéfique" | "maléfique" ; None si pas enclosé ou nature mixte


@dataclass(frozen=True)
class SolarPhenomenonTier:
    planet: str
    gap_degrees: float
    tier: str | None  # "Cazimi" | "Combustion" | "Sous les rayons" | None (>= 15°, "libre")
    # Domicile/exaltation résiste traditionnellement mieux à la combustion
    # ("voyage dans un char à l'ombre du Soleil", Robert Schmidt) — flag
    # documenté, non pondéré dans le classement pour l'instant.
    resists_via_dignity: bool = False


@dataclass(frozen=True)
class PlanetaryCondition:
    planet: str
    bonification_corruption: BonificationCorruption
    enclosure: Enclosure
    solar_phenomenon: SolarPhenomenonTier | None  # None pour Soleil/Lune (pas d'écart au Soleil au sens propre)
    sort_key: tuple[int, int, int, int, int, int, int]
    rank: int  # 1 (plus favorable) à 7


# Niveau 1 (secte) — ordre proposé (meilleur -> moins bon), jugement à
# valider (voir le module docstring) : la préséance bénéfique/maléfique de
# secte sur hors secte est bien attestée (Brennan), l'imbrication exacte
# des paliers neutre/lumière l'est moins.
SECT_ROLE_RANK: dict[str, int] = {
    "Lumière de secte": 0,
    "Bénéfique de secte": 1,
    "Neutre de secte": 2,
    "Maléfique de secte": 3,
    "Neutre hors secte": 4,
    "Hors secte (jour)": 5,
    "Hors secte (nuit)": 5,
    "Bénéfique hors secte": 6,
    "Maléfique hors secte": 7,
}

# Niveau 2 (dignité essentielle majeure) — distinct de
# `docgen.builder.DIGNITY_CATEGORY_ORDER` (ordre d'affichage calqué sur la
# prose des documents de référence, pas un ordre de faveur). Chute classée
# pire qu'Exil (détriment) : jugement documenté, pas universellement
# tranché par les sources (voir module docstring).
MAJOR_DIGNITY_RANK: dict[str, int] = {
    "Domicile": 0,
    "Exaltation": 1,
    "Pérégrin": 2,
    "Pérégrine": 2,
    "Exil (détriment)": 3,
    "Chute": 4,
}

# Niveau 3 (angularité) — non controversé.
HOUSE_QUALITY_RANK: dict[str, int] = {"Angulaire": 0, "Succédente": 1, "Cadente": 2}

# Niveau 4 (phénomène solaire) — décidé explicitement avec l'utilisateur
# (jalon 44) : le cazimi est un renforcement exceptionnel, classé au-dessus
# même d'une planète libre de toute proximité solaire (pas seulement le
# moins mauvais des trois paliers de proximité).
SOLAR_TIER_RANK: dict[str | None, int] = {
    "Cazimi": 0,
    None: 1,  # "libre" : aucun palier de proximité (>= 15°), ou Soleil/Lune eux-mêmes
    "Sous les rayons": 2,
    "Combustion": 3,
}


def _bonification_corruption(planet: PointPosition, others: list[PointPosition]) -> BonificationCorruption:
    """Vénus/Jupiter en conjonction, trigone ou sextile à `planet` ->
    aidé ; Mars/Saturne en conjonction, carré ou opposition -> nui. Un
    bénéfique en carré/opposition, ou un maléfique en trigone/sextile, ne
    compte ni dans un sens ni dans l'autre (asymétrique, pas une règle
    générale "aspect dur = nocif") : sans branche `else`, ces cas sont
    simplement ignorés faute de correspondre à l'une des deux règles."""
    aided: list[AspectInfluence] = []
    harmed: list[AspectInfluence] = []
    for other in others:
        if other.name == planet.name:
            continue
        if other.sign == planet.sign:
            aspect_label = "Conjonction"
        else:
            aspect_label = sign_aspect(planet.sign, other.sign)
            if aspect_label == "Aversion":
                continue
        if other.name in BENEFICS and aspect_label in ("Conjonction", "Trigone", "Sextile"):
            aided.append(AspectInfluence(source=other.name, aspect=aspect_label))
        elif other.name in MALEFICS and aspect_label in ("Conjonction", "Carré", "Opposition"):
            harmed.append(AspectInfluence(source=other.name, aspect=aspect_label))
    return BonificationCorruption(planet=planet.name, aided_by=tuple(aided), harmed_by=tuple(harmed))


def _closest_to_sign_boundary(
    sign: str, near_end: bool, planets_by_name: dict[str, PointPosition], exclude: str
) -> PointPosition | None:
    """Planète la plus proche de la frontière pertinente de `sign` (sa fin
    si `near_end` — le côté qui précède la planète encadrée — sinon son
    début), à moins de `ENCLOSURE_ORB_DEGREES` — None si aucune ne
    satisfait le seuil. Mesure purement intra-signe (`degree_in_sign`), pas
    `angular_gap`/`longitude_of` : on compare une planète à SA PROPRE
    frontière de signe, pas à la longitude d'une autre planète."""
    candidates = [p for p in planets_by_name.values() if p.sign == sign and p.name != exclude]
    if near_end:
        within_orb = [p for p in candidates if 30.0 - p.degree_in_sign < ENCLOSURE_ORB_DEGREES]
        if not within_orb:
            return None
        return min(within_orb, key=lambda p: 30.0 - p.degree_in_sign)
    within_orb = [p for p in candidates if p.degree_in_sign < ENCLOSURE_ORB_DEGREES]
    if not within_orb:
        return None
    return min(within_orb, key=lambda p: p.degree_in_sign)


def _enclosure(planet: PointPosition, planets_by_name: dict[str, PointPosition]) -> Enclosure:
    """Enclosure par signe : une planète dans les 7 derniers degrés du
    signe précédent (proche d'y entrer) ET une planète dans les 7 premiers
    degrés du signe suivant (proche d'en être sortie) — voir le
    commentaire sur `ENCLOSURE_ORB_DEGREES` pour pourquoi ce n'est PAS
    mesuré depuis le degré exact de `planet`. Deux bénéfiques encadrants ->
    "bénéfique" ; deux maléfiques -> "maléfique" (besiegement) ; nature
    mixte -> `category=None` mais `flanking_planets` renseigné quand même."""
    sign_idx = index_of_sign(planet.sign)
    prev_sign = SIGNS[(sign_idx - 1) % 12]
    next_sign = SIGNS[(sign_idx + 1) % 12]

    before = _closest_to_sign_boundary(prev_sign, near_end=True, planets_by_name=planets_by_name, exclude=planet.name)
    after = _closest_to_sign_boundary(next_sign, near_end=False, planets_by_name=planets_by_name, exclude=planet.name)
    if before is None or after is None:
        return Enclosure(planet=planet.name, flanking_planets=None, category=None)

    flanking = (before.name, after.name)
    if before.name in BENEFICS and after.name in BENEFICS:
        category = "bénéfique"
    elif before.name in MALEFICS and after.name in MALEFICS:
        category = "maléfique"
    else:
        category = None
    return Enclosure(planet=planet.name, flanking_planets=flanking, category=category)


def _solar_phenomenon_tier(planet: str, gap_degrees: float, essential_dignity: str | None) -> SolarPhenomenonTier:
    if gap_degrees < CAZIMI_ORB_DEGREES:
        tier = "Cazimi"
    elif gap_degrees < TRUE_COMBUSTION_ORB_DEGREES:
        tier = "Combustion"
    elif gap_degrees < UNDER_RAYS_ORB_DEGREES:
        tier = "Sous les rayons"
    else:
        tier = None
    resists = essential_dignity in ("Domicile", "Exaltation")
    return SolarPhenomenonTier(planet=planet, gap_degrees=gap_degrees, tier=tier, resists_via_dignity=resists)


def _moon_applies_to(moon: PointPosition, planet: PointPosition) -> bool:
    """"La Lune s'applique à `planet`" : une relation d'aspect par signe
    (conjonction incluse) existe déjà entre les deux, et l'écart réel en
    degrés converge (`aspects.is_applying`) — le degré réel ne fait
    qu'affiner une relation déjà valide par signe, jamais la créer seul
    (cohérent avec la règle non-négociable "aspects par signe, pas par
    orbe")."""
    if planet.name == "Lune" or moon.speed is None or planet.speed is None:
        return False
    if moon.sign != planet.sign:
        aspect = sign_aspect(moon.sign, planet.sign)
        if aspect is None or aspect == "Aversion":
            return False
    moon_longitude = longitude_of(moon.sign, moon.degree_in_sign)
    planet_longitude = longitude_of(planet.sign, planet.degree_in_sign)
    return is_applying(moon_longitude, moon.speed, planet_longitude, planet.speed)


def _configuration_score(bc: BonificationCorruption, enclosure: Enclosure) -> int:
    """Niveau 6 du classement : un simple départage (jamais un score
    additif qui écraserait les niveaux précédents dans le tri
    lexicographique). Plus bas = plus favorable."""
    score = len(bc.harmed_by) - len(bc.aided_by)
    if enclosure.category == "maléfique":
        score += 1
    elif enclosure.category == "bénéfique":
        score -= 1
    return score


def compute_planetary_conditions(
    planets: list[PointPosition],
    mutual_receptions: list[MutualReception],
    solar_proximity: list[SolarProximity],
) -> list[PlanetaryCondition]:
    """Grille de condition planétaire complète pour les 7 planètes
    classiques, dans le même ordre que `planets` en entrée (pas dans
    l'ordre du classement — `rank` porte l'information de classement,
    voir `PlanetaryCondition`)."""
    planets_by_name = {p.name: p for p in planets}
    solar_gap_by_name = {sp.planet: sp.gap_degrees for sp in solar_proximity}
    reception_partners = {r.planet_a for r in mutual_receptions} | {r.planet_b for r in mutual_receptions}
    moon = planets_by_name.get("Lune")
    planet_order = list(CLASSICAL_PLANETS.keys())

    conditions = []
    for planet in planets:
        others = [p for p in planets if p.name != planet.name]
        bc = _bonification_corruption(planet, others)
        enc = _enclosure(planet, planets_by_name)

        gap = solar_gap_by_name.get(planet.name)
        solar_tier = (
            _solar_phenomenon_tier(planet.name, gap, planet.essential_dignity) if gap is not None else None
        )

        sect_rank = SECT_ROLE_RANK[planet.sect_role]
        major = MAJOR_DIGNITY_RANK[planet.essential_dignity]
        has_minor_dignity = bool(planet.triplicity_dignity or planet.bound_dignity or planet.decan_dignity)
        minor_bonus = 0 if has_minor_dignity else 1
        reception_bonus = 0 if planet.name in reception_partners else 1
        dignity_rank = major * 4 + minor_bonus * 2 + reception_bonus
        angularity_rank = HOUSE_QUALITY_RANK[planet.house_quality]
        solar_rank = SOLAR_TIER_RANK[solar_tier.tier if solar_tier else None]
        lunar_rank = 1
        if moon is not None and planet.name != "Lune":
            lunar_rank = 0 if _moon_applies_to(moon, planet) else 1
        configuration_rank = _configuration_score(bc, enc)
        tie_break = planet_order.index(planet.name)

        sort_key = (sect_rank, dignity_rank, angularity_rank, solar_rank, lunar_rank, configuration_rank, tie_break)

        conditions.append(
            PlanetaryCondition(
                planet=planet.name,
                bonification_corruption=bc,
                enclosure=enc,
                solar_phenomenon=solar_tier,
                sort_key=sort_key,
                rank=0,
            )
        )

    ranked = sorted(conditions, key=lambda c: c.sort_key)
    ranked_with_rank = [replace(condition, rank=idx) for idx, condition in enumerate(ranked, start=1)]
    by_name = {c.planet: c for c in ranked_with_rank}
    return [by_name[p.name] for p in planets]
