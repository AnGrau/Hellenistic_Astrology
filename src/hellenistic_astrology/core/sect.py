def is_diurnal(sun_house: int) -> bool:
    """Secte de la carte : diurne si le Soleil est au-dessus de l'horizon,
    c'est-à-dire dans les maisons 7 à 12 (en signes entiers)."""
    return sun_house in range(7, 13)
