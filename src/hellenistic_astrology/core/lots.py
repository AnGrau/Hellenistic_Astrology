def part_of_fortune(ascendant: float, sun: float, moon: float, diurnal: bool) -> float:
    if diurnal:
        return (ascendant + moon - sun) % 360
    return (ascendant + sun - moon) % 360


def part_of_spirit(ascendant: float, sun: float, moon: float, diurnal: bool) -> float:
    if diurnal:
        return (ascendant + sun - moon) % 360
    return (ascendant + moon - sun) % 360


def part_of_eros(ascendant: float, venus: float, spirit: float, diurnal: bool) -> float:
    """Part d'Éros : réutilise Vénus et la Part de l'Esprit, formule inversée
    selon la secte (même schéma que Fortune/Esprit avec Soleil/Lune).
    Vérifiée contre les deux thèmes de référence."""
    if diurnal:
        return (ascendant + venus - spirit) % 360
    return (ascendant + spirit - venus) % 360
