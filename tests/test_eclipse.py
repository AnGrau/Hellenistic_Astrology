import pytest

from hellenistic_astrology.core.eclipse import (
    LUNAR_ECLIPSE_ORB_DEGREES,
    SOLAR_ECLIPSE_ORB_DEGREES,
    eclipse_configuration,
)


def test_exact_new_moon_conjunct_north_node_is_solar_eclipse():
    result = eclipse_configuration(sun_longitude=0.0, moon_longitude=1.0, north_node_longitude=0.5)
    assert result.is_eclipse is True
    assert result.eclipse_type == "solaire"
    assert result.syzygy_type == "Nouvelle Lune"
    assert result.closer_node == "Nœud Nord"


def test_exact_full_moon_conjunct_south_node_is_lunar_eclipse():
    # Lune à 180° du Soleil (Pleine Lune exacte) et conjointe au Nœud Sud
    # (donc à 180° du Nœud Nord, situé à 0°).
    result = eclipse_configuration(sun_longitude=0.0, moon_longitude=180.0, north_node_longitude=0.0)
    assert result.is_eclipse is True
    assert result.eclipse_type == "lunaire"
    assert result.syzygy_type == "Pleine Lune"
    assert result.closer_node == "Nœud Sud"


def test_new_moon_but_far_from_node_is_not_eclipse():
    result = eclipse_configuration(sun_longitude=0.0, moon_longitude=2.0, north_node_longitude=90.0)
    assert result.is_eclipse is False
    assert result.eclipse_type is None


def test_near_node_but_far_from_syzygy_is_not_eclipse():
    # Lune proche du Nœud Sud mais en quadrature avec le Soleil (ni Nouvelle
    # ni Pleine Lune) : cas du thème d'Anthony (Lune proche du Nœud, phase
    # disséminatrice).
    result = eclipse_configuration(sun_longitude=0.0, moon_longitude=90.5, north_node_longitude=270.5)
    assert result.is_eclipse is False
    assert result.eclipse_type is None


def test_solar_and_lunar_thresholds_are_the_documented_astronomical_limits():
    assert SOLAR_ECLIPSE_ORB_DEGREES == 18.4
    assert LUNAR_ECLIPSE_ORB_DEGREES == 12.2


@pytest.mark.parametrize(
    "name, sun_lon, moon_lon, node_lon, expected_node_gap, expected_syzygy_gap, expected_closer_node",
    [
        # Anthony : Lune quasi conjointe au Nœud Sud (moins de 1°), mais très
        # loin de toute syzygie (phase disséminatrice) -> pas d'éclipse.
        ("anthony", 238.17975, 147.70712, 328.2502, 0.543, 89.527, "Nœud Sud"),
        # Liam : Lune loin des deux Nœuds et à ~26,5° de la Pleine Lune ->
        # pas d'éclipse non plus, sur les deux critères indépendamment.
        ("liam", 206.27595, 52.80607, 13.61568, 39.190, 26.530, "Nœud Nord"),
    ],
)
def test_reference_charts_confirm_no_eclipse(
    name, sun_lon, moon_lon, node_lon, expected_node_gap, expected_syzygy_gap, expected_closer_node
):
    result = eclipse_configuration(sun_lon, moon_lon, node_lon)
    assert result.is_eclipse is False
    assert result.closer_node == expected_closer_node
    assert result.node_gap_degrees == pytest.approx(expected_node_gap, abs=0.01)
    assert result.syzygy_gap_degrees == pytest.approx(expected_syzygy_gap, abs=0.01)
