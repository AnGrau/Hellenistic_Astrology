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
