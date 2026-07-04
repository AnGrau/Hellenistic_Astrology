from dataclasses import dataclass

# Huit phases de lunaison (Dane Rudhyar, "The Lunation Cycle", 1967) : l'écart
# Lune-Soleil (0-360°, dans le sens du mouvement propre de la Lune, plus
# rapide que le Soleil ; 0° = conjonction/Nouvelle Lune, 180° = opposition/
# Pleine Lune) est divisé en 8 segments égaux de 45°. Vérifié contre deux
# sources indépendantes et cohérentes entre elles (Cafe Astrology ; recoupé
# par plusieurs synthèses d'astrologie francophone utilisant la même
# terminologie et les mêmes bornes) faute de fixture de vérité terrain fiable
# — voir la remarque ci-dessous sur la divergence relevée avec le thème de
# Liam. Noms en français : "disséminatrice" est celui employé tel quel par les
# deux documents de référence ; les autres suivent la même convention
# (adjectif accordé au féminin, comme pour "Lune").
#
# Divergence relevée et non reproduite : le document de référence de Liam
# qualifie son écart Soleil-Lune (~206,5°, soit ~26° après l'opposition
# exacte) de "disséminatrice", alors que ces bornes (vérifiées
# indépendamment, et qui reproduisent exactement la phrase du document
# d'Anthony — écart ~269,5°, à 0,5° de la frontière 225-270/270-315, décrit
# comme "disséminatrice, à la limite du dernier quartier") le classent en
# "Pleine" (180-225°). Traité comme une erreur isolée du document de Liam
# (même méthode que les incohérences précédentes : secte, Nœud Sud, MC,
# réception mutuelle), pas comme une divergence de système à arbitrer.
LUNATION_PHASES: list[tuple[float, str]] = [
    (45.0, "nouvelle"),
    (90.0, "croissante"),
    (135.0, "premier quartier"),
    (180.0, "gibbeuse"),
    (225.0, "pleine"),
    (270.0, "disséminatrice"),
    (315.0, "dernier quartier"),
    (360.0, "balsamique"),
]


@dataclass(frozen=True)
class LunationPhase:
    name: str
    gap_degrees: float


def lunation_phase(sun_longitude: float, moon_longitude: float) -> LunationPhase:
    """Phase de lunaison natale de `moon_longitude` par rapport à `sun_longitude`."""
    gap = (moon_longitude - sun_longitude) % 360
    for upper_bound, name in LUNATION_PHASES:
        if gap < upper_bound:
            return LunationPhase(name=name, gap_degrees=gap)
    raise AssertionError("Table de phases incomplète — devrait couvrir [0, 360).")
