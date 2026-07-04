import json
from dataclasses import asdict, dataclass, field

from .dignities import Rulership


@dataclass(frozen=True)
class PointPosition:
    name: str
    sign: str
    degree_in_sign: float
    house: int
    retrograde: bool | None = None
    essential_dignity: str | None = None
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
    rulerships: list[Rulership] = field(default_factory=list)
    # Types concrets définis dans core.aspects (SignCluster, ClusterAspect) ;
    # pas d'import direct ici pour éviter une dépendance circulaire
    # (aspects.py importe déjà PointPosition depuis ce module).
    clusters: list = field(default_factory=list)
    cluster_aspects: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def planet(self, name: str) -> PointPosition:
        for p in self.planets:
            if p.name == name:
                return p
        raise KeyError(name)
