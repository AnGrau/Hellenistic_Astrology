from dataclasses import dataclass

# Limites astronomiques standard d'éclipse partielle (Soleil ou Lune à moins
# de ce seuil d'un Nœud au moment de la syzygie pour qu'une éclipse partielle
# se produise réellement), déjà notées dans CLAUDE.md. Adaptées ici à un
# instantané natal (pas un calcul d'éclipse réelle, qui nécessiterait une
# éphéméride d'éclipses) : un thème est dit en "configuration d'éclipse" si
# la Lune est simultanément proche d'un Nœud ET proche de la syzygie
# Soleil-Lune correspondante (conjonction pour une configuration solaire,
# opposition pour une configuration lunaire), aux mêmes seuils. Décision
# validée explicitement avec l'utilisateur (jalon 25) : ni Anthony ni Liam
# n'ont de configuration d'éclipse (les deux échouent largement sur au moins
# un des deux critères), donc ce choix de seuils n'est pas calibrable sur un
# cas positif réel — seule la cohérence avec les limites astronomiques
# standard le justifie.
SOLAR_ECLIPSE_ORB_DEGREES = 18.4
LUNAR_ECLIPSE_ORB_DEGREES = 12.2


@dataclass(frozen=True)
class EclipseConfiguration:
    is_eclipse: bool
    eclipse_type: str | None  # "solaire" | "lunaire", None si pas de configuration
    node_gap_degrees: float  # écart réel Lune-Nœud le plus proche (Nord ou Sud)
    closer_node: str  # "Nœud Nord" | "Nœud Sud" : celui dont `node_gap_degrees` se rapproche
    syzygy_type: str  # "Nouvelle Lune" | "Pleine Lune" : la syzygie la plus proche
    syzygy_gap_degrees: float  # écart réel Soleil-Lune à cette syzygie


def eclipse_configuration(
    sun_longitude: float, moon_longitude: float, north_node_longitude: float
) -> EclipseConfiguration:
    # Import tardif : évite le cycle eclipse -> aspects -> observation ->
    # eclipse (aspects importe PointPosition depuis observation, qui importe
    # EclipseConfiguration d'ici) — même contournement que
    # dignities.solar_proximity.
    from .aspects import angular_gap

    south_node_longitude = (north_node_longitude + 180) % 360
    north_node_gap = angular_gap(moon_longitude, north_node_longitude)
    south_node_gap = angular_gap(moon_longitude, south_node_longitude)
    if north_node_gap <= south_node_gap:
        node_gap, closer_node = north_node_gap, "Nœud Nord"
    else:
        node_gap, closer_node = south_node_gap, "Nœud Sud"

    # angular_gap est symétrique (0-180°) : c'est déjà la distance à la
    # conjonction (Nouvelle Lune) ; la distance à l'opposition (Pleine Lune)
    # est son complément à 180°.
    distance_to_new_moon = angular_gap(sun_longitude, moon_longitude)
    distance_to_full_moon = 180 - distance_to_new_moon
    if distance_to_new_moon <= distance_to_full_moon:
        syzygy_type, syzygy_gap, threshold, eclipse_type = (
            "Nouvelle Lune", distance_to_new_moon, SOLAR_ECLIPSE_ORB_DEGREES, "solaire",
        )
    else:
        syzygy_type, syzygy_gap, threshold, eclipse_type = (
            "Pleine Lune", distance_to_full_moon, LUNAR_ECLIPSE_ORB_DEGREES, "lunaire",
        )

    is_eclipse = node_gap < threshold and syzygy_gap < threshold
    return EclipseConfiguration(
        is_eclipse=is_eclipse,
        eclipse_type=eclipse_type if is_eclipse else None,
        node_gap_degrees=node_gap,
        closer_node=closer_node,
        syzygy_type=syzygy_type,
        syzygy_gap_degrees=syzygy_gap,
    )
