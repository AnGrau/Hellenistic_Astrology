import json
from dataclasses import asdict, dataclass, field

from .dignities import MutualReception, Rulership
from .zodiacal_releasing import ReleasingChapter


@dataclass(frozen=True)
class PointPosition:
    name: str
    sign: str
    degree_in_sign: float
    house: int
    # Métadonnées géométriques universelles (calculées pour tous les points,
    # contrairement aux dignités ci-dessous qui ne concernent que les
    # planètes classiques) : élément (réutilise dignities.SIGN_TRIPLICITY),
    # modalité (houses.MODALITY_BY_SIGN) et angularité (houses.house_quality).
    element: str | None = None
    modality: str | None = None
    house_quality: str | None = None
    retrograde: bool | None = None
    essential_dignity: str | None = None
    triplicity_dignity: str | None = None
    bound_dignity: str | None = None
    decan_dignity: str | None = None
    sect_role: str | None = None
    # Vitesse écliptique signée (°/jour), renseignée uniquement pour les
    # planètes classiques : nécessaire à la règle des 3° hors-signe
    # (core.aspects). None pour l'Ascendant, le MC et les Lots.
    speed: float | None = None


@dataclass(frozen=True)
class Observation:
    """Relevé factuel de la phase 1 (Observation), sans interprétation.

    Frontière explicite entre le module de calcul (core/) et la génération
    du document (docgen/) : docgen ne doit consommer que cet objet.
    """

    name: str
    sect: str  # "diurne" | "nocturne"
    ascendant: PointPosition
    midheaven: PointPosition
    planets: list[PointPosition] = field(default_factory=list)
    part_of_fortune: PointPosition | None = None
    part_of_spirit: PointPosition | None = None
    part_of_eros: PointPosition | None = None
    north_node: PointPosition | None = None
    south_node: PointPosition | None = None
    rulerships: list[Rulership] = field(default_factory=list)
    mutual_receptions: list[MutualReception] = field(default_factory=list)
    # Tous les points ci-dessus, dans l'ordre canonique d'affichage (celui du
    # tableau des positions des documents de référence) : source unique
    # utilisée par docgen et par le calcul des amas/aspects, pour éviter que
    # les deux ne dérivent d'un ordre reconstruit séparément.
    all_points: list[PointPosition] = field(default_factory=list)
    # Types concrets définis dans core.aspects (SignCluster, ClusterAspect) ;
    # pas d'import direct ici pour éviter une dépendance circulaire
    # (aspects.py importe déjà PointPosition depuis ce module).
    clusters: list = field(default_factory=list)
    cluster_aspects: list = field(default_factory=list)
    # Libération zodiacale, niveaux L1+L2, de la naissance à un horizon
    # arbitraire (voir core.chart) — voir core.zodiacal_releasing pour
    # l'algorithme et docgen.builder pour le rendu.
    zodiacal_releasing_fortune: list[ReleasingChapter] = field(default_factory=list)
    zodiacal_releasing_spirit: list[ReleasingChapter] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, **kwargs) -> str:
        # `default=str` : les dates de libération zodiacale (datetime) ne
        # sont pas sérialisables nativement par json.dumps.
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str, **kwargs)

    def planet(self, name: str) -> PointPosition:
        for p in self.planets:
            if p.name == name:
                return p
        raise KeyError(name)

    def point(self, name: str) -> PointPosition:
        for p in self.all_points:
            if p.name == name:
                return p
        raise KeyError(name)
