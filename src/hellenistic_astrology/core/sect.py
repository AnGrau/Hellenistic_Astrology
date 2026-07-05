"""Secte de la carte (diurne/nocturne) et rôle de secte par planète
classique — la position du Soleil détermine la secte, qui à son tour
détermine les formules des Lots (`lots.py`) et le rôle de chaque planète."""


def is_diurnal(sun_house: int) -> bool:
    """Secte de la carte : diurne si le Soleil est au-dessus de l'horizon,
    c'est-à-dire dans les maisons 7 à 12 (en signes entiers)."""
    return sun_house in range(7, 13)


# nature : "luminary" (Soleil/Lune), "benefic" (Vénus/Jupiter),
# "malefic" (Mars/Saturne), "neutral" (Mercure).
# affinity : "diurnal" ou "nocturnal" (secte naturelle de la planète),
# ignoré pour les planètes neutres.
_SECT_NATURE: dict[str, tuple[str, str | None]] = {
    "Soleil": ("luminary", "diurnal"),
    "Lune": ("luminary", "nocturnal"),
    "Mercure": ("neutral", None),
    "Vénus": ("benefic", "nocturnal"),
    "Jupiter": ("benefic", "diurnal"),
    "Mars": ("malefic", "nocturnal"),
    "Saturne": ("malefic", "diurnal"),
}

# Classification bénéfique/maléfique seule (sans la dimension de secte),
# dérivée de `_SECT_NATURE` plutôt que dupliquée : source unique de vérité
# pour tout module qui a besoin de cette classification sans passer par
# `sect_role()` (ex. `core.condition`, jalon 44 — bonification/corruption
# par aspect, qui a besoin de savoir "Vénus/Jupiter bénéfiques,
# Mars/Saturne maléfiques" indépendamment de toute secte de carte).
BENEFICS = frozenset(planet for planet, (nature, _) in _SECT_NATURE.items() if nature == "benefic")
MALEFICS = frozenset(planet for planet, (nature, _) in _SECT_NATURE.items() if nature == "malefic")


def mercury_is_morning_star(mercury_longitude: float, sun_longitude: float) -> bool:
    """True si Mercure est étoile du matin (se lève avant le Soleil), False
    si étoile du soir (se lève/se couche après lui) — seule planète dont
    l'affinité de secte n'est pas fixe (`_SECT_NATURE` la note "neutral"),
    mais dépend de sa phase héliaque à la naissance (doctrine hellénistique,
    ex. Vettius Valens/Rhetorius tels que rapportés par Chris Brennan ;
    aucun des deux thèmes de référence ne documente ce point explicitement,
    voir CLAUDE.md jalon 38).

    La rotation diurne fait culminer/lever plus tôt l'astre dont
    l'ascension droite (assimilée ici à la longitude écliptique, latitude
    négligeable pour Mercure) est la plus petite. Mercure "derrière" le
    Soleil dans l'ordre du zodiaque (longitude moindre) se lève donc avant
    lui — étoile du matin ; "devant" le Soleil (longitude supérieure), il
    se lève et se couche après lui — étoile du soir, visible au
    crépuscule."""
    diff = (mercury_longitude - sun_longitude + 180) % 360 - 180
    return diff < 0


def sect_role(planet: str, diurnal_chart: bool, mercury_morning_star: bool | None = None) -> str:
    """Rôle de secte d'une planète classique dans une carte donnée.

    Règle symétrique : le luminaire dont la secte naturelle ne correspond
    pas à celle de la carte est toujours « Hors secte », qu'il s'agisse du
    Soleil de nuit ou de la Lune de jour (pas de cas « neutre » pour les
    luminaires).

    Mercure (seule planète "neutral" de `_SECT_NATURE`) n'a pas d'affinité
    fixe : son affinité pour cet appel est déterminée par
    `mercury_morning_star` (obligatoire dans ce cas, voir
    `mercury_is_morning_star`) — étoile du matin => affinité diurne (rejoint
    Jupiter/Saturne dans un thème de jour), étoile du soir => affinité
    nocturne (rejoint Vénus/Mars dans un thème de nuit). Le résultat suit la
    même logique de correspondance que les autres planètes, avec le
    qualificatif "Neutre" plutôt que "Bénéfique"/"Maléfique".
    """
    nature, affinity = _SECT_NATURE[planet]
    chart_affinity = "diurnal" if diurnal_chart else "nocturnal"

    if nature == "neutral":
        if mercury_morning_star is None:
            raise ValueError("mercury_morning_star est requis pour une planète neutre (Mercure)")
        affinity = "diurnal" if mercury_morning_star else "nocturnal"
        matches = affinity == chart_affinity
        return "Neutre de secte" if matches else "Neutre hors secte"

    matches = affinity == chart_affinity

    if nature == "luminary":
        if matches:
            return "Lumière de secte"
        return f"Hors secte ({'jour' if chart_affinity == 'diurnal' else 'nuit'})"

    label = "Bénéfique" if nature == "benefic" else "Maléfique"
    return f"{label} de secte" if matches else f"{label} hors secte"
