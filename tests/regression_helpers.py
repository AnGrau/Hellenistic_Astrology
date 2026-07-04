import json
from datetime import date, time
from pathlib import Path

from hellenistic_astrology.core.observation import Observation, PointPosition
from hellenistic_astrology.core.timezone import BirthData

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Tolérance de comparaison sur les degrés dans le signe : 3 arcminutes,
# pour absorber l'arrondi des données de référence (déjà arrondies à la
# minute d'arc) et un éventuel écart Moshier / Swiss Ephemeris fichier.
DEGREE_TOLERANCE = 0.05


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def birth_data_from_fixture(fixture: dict) -> BirthData:
    bd = fixture["birth_data"]
    return BirthData(
        name=bd["name"],
        latitude=bd["latitude"],
        longitude=bd["longitude"],
        local_date=date.fromisoformat(bd["local_date"]),
        local_time=time.fromisoformat(bd["local_time"]),
        tz_name=bd["tz_name"],
    )


def assert_point_matches(actual: PointPosition, expected: dict, label: str) -> None:
    assert actual.sign == expected["sign"], f"{label} : signe {actual.sign} != {expected['sign']}"
    assert actual.house == expected["house"], f"{label} : maison {actual.house} != {expected['house']}"
    diff = abs(actual.degree_in_sign - expected["degree_in_sign"])
    assert diff <= DEGREE_TOLERANCE, (
        f"{label} : degré {actual.degree_in_sign} != {expected['degree_in_sign']} (écart {diff})"
    )
    if "retrograde" in expected:
        assert actual.retrograde == expected["retrograde"], (
            f"{label} : rétrograde {actual.retrograde} != {expected['retrograde']}"
        )
    if "essential_dignity" in expected:
        assert actual.essential_dignity == expected["essential_dignity"], (
            f"{label} : dignité {actual.essential_dignity} != {expected['essential_dignity']}"
        )
    if "sect_role" in expected:
        assert actual.sect_role == expected["sect_role"], (
            f"{label} : rôle de secte {actual.sect_role} != {expected['sect_role']}"
        )


def assert_rulerships_match(observation: Observation, fixture: dict) -> None:
    by_planet = {r.planet: r for r in observation.rulerships}
    for planet, expected in fixture["rulerships"].items():
        actual = by_planet[planet]
        assert list(actual.domicile_signs) == expected["domicile_signs"], (
            f"{planet} : domiciles {actual.domicile_signs} != {expected['domicile_signs']}"
        )
        assert list(actual.houses_governed) == expected["houses_governed"], (
            f"{planet} : maisons régies {actual.houses_governed} != {expected['houses_governed']}"
        )


def assert_clusters_match(observation: Observation, fixture: dict) -> None:
    actual = [
        {"sign": c.sign, "house": c.house, "members": list(c.members)}
        for c in observation.clusters
    ]
    assert actual == fixture["clusters"], f"amas {actual} != {fixture['clusters']}"


def assert_cluster_aspects_match(observation: Observation, fixture: dict) -> None:
    actual = [
        {
            "sign_a": a.sign_a,
            "sign_b": a.sign_b,
            "aspect": a.aspect,
            "boundary_exception": a.boundary_exception,
        }
        for a in observation.cluster_aspects
    ]
    assert actual == fixture["cluster_aspects"], (
        f"aspects entre amas {actual} != {fixture['cluster_aspects']}"
    )


def assert_observation_matches(observation: Observation, fixture: dict) -> None:
    assert observation.sect == fixture["sect"], (
        f"secte {observation.sect} != {fixture['sect']}"
    )
    assert_point_matches(observation.ascendant, fixture["ascendant"], "Ascendant")
    assert_point_matches(observation.midheaven, fixture["midheaven"], "Milieu du Ciel")
    for name, expected in fixture["planets"].items():
        assert_point_matches(observation.planet(name), expected, name)
    assert_point_matches(observation.part_of_fortune, fixture["part_of_fortune"], "Part de Fortune")
    assert_point_matches(observation.part_of_spirit, fixture["part_of_spirit"], "Part de l'Esprit")
    assert_rulerships_match(observation, fixture)
    assert_clusters_match(observation, fixture)
    assert_cluster_aspects_match(observation, fixture)
