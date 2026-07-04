"""Aspects ptoléméens par signe : regroupement des points en amas
(`SignCluster`) par signe, aspect entre chaque paire d'amas, et la règle
des 3° hors-signe (`out_of_sign_conjunction`) pour les cas limites."""

from dataclasses import dataclass

from .houses import index_of_sign, longitude_of
from .observation import PointPosition

BOUNDARY_ORB_DEGREES = 3.0

# Distance en signes (0-11) -> aspect ptoléméen par signe. Une distance de 0
# (même signe) n'est pas un "aspect" au sens de cette table : elle relève du
# regroupement en amas (SignCluster), pas d'une relation entre deux amas.
_ASPECT_BY_DISTANCE: dict[int, str] = {
    1: "Aversion",
    2: "Sextile",
    3: "Carré",
    4: "Trigone",
    5: "Aversion",
    6: "Opposition",
    7: "Aversion",
    8: "Trigone",
    9: "Carré",
    10: "Sextile",
    11: "Aversion",
}


def sign_distance(sign_a: str, sign_b: str) -> int:
    return (index_of_sign(sign_b) - index_of_sign(sign_a)) % 12


def sign_aspect(sign_a: str, sign_b: str) -> str | None:
    """Aspect ptoléméen par signe entre deux signes distincts.

    Renvoie None si sign_a == sign_b (même amas, pas de relation à calculer).
    """
    distance = sign_distance(sign_a, sign_b)
    if distance == 0:
        return None
    return _ASPECT_BY_DISTANCE[distance]


def angular_gap(longitude_a: float, longitude_b: float) -> float:
    """Écart angulaire réel (0-180°) entre deux longitudes écliptiques."""
    diff = (longitude_b - longitude_a) % 360
    return diff if diff <= 180 else 360 - diff


def _is_applying(longitude_a: float, speed_a: float, longitude_b: float, speed_b: float) -> bool:
    gap = (longitude_b - longitude_a) % 360
    if gap > 180:
        gap -= 360  # écart signé dans (-180, 180] : positif si B est "devant" A.
    relative_speed = speed_b - speed_a
    return (gap > 0 and relative_speed < 0) or (gap < 0 and relative_speed > 0)


def out_of_sign_conjunction(point_a: PointPosition, point_b: PointPosition) -> bool:
    """Règle des 3° hors-signe (CLAUDE.md) : deux planètes classiques dans des
    signes adjacents sont malgré tout considérées en aspect si la plus
    rapide applique à moins de 3° de la plus lente.

    Porte sur la proximité écliptique réelle à la frontière commune, pas sur
    une coïncidence de degré-dans-signe (voir le cas Mercure/Vénus d'Anthony,
    où les degrés-dans-signe sont proches mais l'écart réel dépasse 30°).

    Ne s'applique qu'aux planètes classiques (speed renseigné) : la notion de
    planète "la plus rapide qui applique" ne s'étend pas aux angles ou aux
    Lots dans la formulation de CLAUDE.md.
    """
    if point_a.speed is None or point_b.speed is None:
        return False
    if sign_distance(point_a.sign, point_b.sign) not in (1, 11):
        return False

    longitude_a = longitude_of(point_a.sign, point_a.degree_in_sign)
    longitude_b = longitude_of(point_b.sign, point_b.degree_in_sign)
    if angular_gap(longitude_a, longitude_b) >= BOUNDARY_ORB_DEGREES:
        return False

    return _is_applying(longitude_a, point_a.speed, longitude_b, point_b.speed)


@dataclass(frozen=True)
class SignCluster:
    sign: str
    house: int
    members: tuple[str, ...]


def build_clusters(points: list[PointPosition]) -> list[SignCluster]:
    by_sign: dict[str, list[PointPosition]] = {}
    for point in points:
        by_sign.setdefault(point.sign, []).append(point)

    clusters = [
        SignCluster(sign=sign, house=members[0].house, members=tuple(m.name for m in members))
        for sign, members in by_sign.items()
    ]
    return sorted(clusters, key=lambda c: index_of_sign(c.sign))


@dataclass(frozen=True)
class ClusterAspect:
    sign_a: str
    sign_b: str
    aspect: str  # "Sextile" | "Carré" | "Trigone" | "Opposition" | "Aversion"
    # True si une aversion a été requalifiée par la règle des 3° hors-signe
    # entre au moins une paire de membres des deux amas.
    boundary_exception: bool = False


def compute_cluster_aspects(clusters: list[SignCluster], points: list[PointPosition]) -> list[ClusterAspect]:
    points_by_name = {p.name: p for p in points}
    result = []
    for i, cluster_a in enumerate(clusters):
        for cluster_b in clusters[i + 1 :]:
            aspect = sign_aspect(cluster_a.sign, cluster_b.sign)
            boundary_exception = False
            if aspect == "Aversion":
                boundary_exception = any(
                    out_of_sign_conjunction(points_by_name[name_a], points_by_name[name_b])
                    for name_a in cluster_a.members
                    for name_b in cluster_b.members
                    if points_by_name[name_a].speed is not None
                    and points_by_name[name_b].speed is not None
                )
            result.append(
                ClusterAspect(
                    sign_a=cluster_a.sign,
                    sign_b=cluster_b.sign,
                    aspect=aspect,
                    boundary_exception=boundary_exception,
                )
            )
    return result
