from hellenistic_astrology.core.chart import build_observation

from .regression_helpers import assert_observation_matches, birth_data_from_fixture, load_fixture


def test_liam_observation_matches_reference():
    fixture = load_fixture("liam")
    birth = birth_data_from_fixture(fixture)

    observation = build_observation(birth)

    assert_observation_matches(observation, fixture)


def test_liam_ascendant_element_modality_house_quality():
    # Ascendant Verseau : Air / Fixe / maison 1 (angulaire), confirmé contre
    # le texte du document de référence (Phase 2, jalon 19).
    fixture = load_fixture("liam")
    observation = build_observation(birth_data_from_fixture(fixture))

    assert observation.ascendant.element == "Air"
    assert observation.ascendant.modality == "Fixe"
    assert observation.ascendant.house_quality == "Angulaire"


def test_liam_solar_proximity_matches_reference():
    # Écarts au Soleil confirmés contre le texte du document de référence
    # (Phase 2, jalon 20) : Jupiter 2°18', Mercure 19°41'.
    fixture = load_fixture("liam")
    observation = build_observation(birth_data_from_fixture(fixture))
    gaps = {sp.planet: sp.gap_degrees for sp in observation.solar_proximity}

    assert abs(gaps["Jupiter"] - (2 + 18 / 60)) < 0.1
    assert abs(gaps["Mercure"] - (19 + 41 / 60)) < 0.1
