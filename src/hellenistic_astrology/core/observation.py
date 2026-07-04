import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class PointPosition:
    name: str
    sign: str
    degree_in_sign: float
    house: int
    retrograde: bool | None = None


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

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def planet(self, name: str) -> PointPosition:
        for p in self.planets:
            if p.name == name:
                return p
        raise KeyError(name)
