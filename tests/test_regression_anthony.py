from hellenistic_astrology.core.chart import build_observation

from .regression_helpers import assert_observation_matches, birth_data_from_fixture, load_fixture


def test_anthony_observation_matches_reference():
    fixture = load_fixture("anthony")
    birth = birth_data_from_fixture(fixture)

    observation = build_observation(birth)

    assert_observation_matches(observation, fixture)
