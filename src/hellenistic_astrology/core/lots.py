def part_of_fortune(ascendant: float, sun: float, moon: float, diurnal: bool) -> float:
    if diurnal:
        return (ascendant + moon - sun) % 360
    return (ascendant + sun - moon) % 360


def part_of_spirit(ascendant: float, sun: float, moon: float, diurnal: bool) -> float:
    if diurnal:
        return (ascendant + sun - moon) % 360
    return (ascendant + moon - sun) % 360
