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


def sect_role(planet: str, diurnal_chart: bool) -> str:
    """Rôle de secte d'une planète classique dans une carte donnée.

    Règle symétrique : le luminaire dont la secte naturelle ne correspond
    pas à celle de la carte est toujours « Hors secte », qu'il s'agisse du
    Soleil de nuit ou de la Lune de jour (pas de cas « neutre » pour les
    luminaires).
    """
    nature, affinity = _SECT_NATURE[planet]
    chart_affinity = "diurnal" if diurnal_chart else "nocturnal"

    if nature == "neutral":
        return "Neutre"

    matches = affinity == chart_affinity

    if nature == "luminary":
        if matches:
            return "Lumière de secte"
        return f"Hors secte ({'jour' if chart_affinity == 'diurnal' else 'nuit'})"

    label = "Bénéfique" if nature == "benefic" else "Maléfique"
    return f"{label} de secte" if matches else f"{label} hors secte"
