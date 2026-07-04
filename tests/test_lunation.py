import pytest

from hellenistic_astrology.core.lunation import LunationPhase, lunation_phase


@pytest.mark.parametrize(
    "sun_longitude, moon_longitude, expected_name, expected_gap",
    [
        (0.0, 10.0, "nouvelle", 10.0),
        (0.0, 44.999, "nouvelle", 44.999),
        (0.0, 45.0, "croissante", 45.0),
        (0.0, 90.0, "premier quartier", 90.0),
        (0.0, 135.0, "gibbeuse", 135.0),
        (0.0, 180.0, "pleine", 180.0),
        (0.0, 225.0, "disséminatrice", 225.0),
        (0.0, 270.0, "dernier quartier", 270.0),
        (0.0, 315.0, "balsamique", 315.0),
        (0.0, 359.999, "balsamique", 359.999),
        # L'écart s'enroule (Lune plus rapide que le Soleil) : Soleil à 350°,
        # Lune à 10° -> écart de 20°, pas -340°.
        (350.0, 10.0, "nouvelle", 20.0),
    ],
)
def test_lunation_phase_boundaries(sun_longitude, moon_longitude, expected_name, expected_gap):
    result = lunation_phase(sun_longitude, moon_longitude)
    assert result == LunationPhase(name=expected_name, gap_degrees=pytest.approx(expected_gap))


def test_lunation_phase_reference_charts_gap_degrees():
    # Écart Soleil-Lune recoupé contre les deux documents de référence :
    # Anthony (~269,5°, "proche de 270°") et Liam (~206,5°, "environ 206°").
    # Solaire uniquement, sans dépendance à build_observation : Sun/Moon
    # longitudes reprises telles que calculées par ephemeris (voir fixtures).
    anthony_sun = 7 * 30 + 28.1833  # Scorpion
    anthony_moon = 4 * 30 + 27.7  # Lion
    result = lunation_phase(anthony_sun, anthony_moon)
    assert result.gap_degrees == pytest.approx(269.52, abs=0.01)
    # Confirme la phrase du document ("disséminatrice, à la limite du dernier
    # quartier") : à 0,5° de la frontière 225-270/270-315.
    assert result.name == "disséminatrice"

    liam_sun = 6 * 30 + 26.2833  # Balance
    liam_moon = 1 * 30 + 22.8  # Taureau
    result = lunation_phase(liam_sun, liam_moon)
    assert result.gap_degrees == pytest.approx(206.52, abs=0.01)
    # Divergence assumée : le document de Liam qualifie cet écart de
    # "disséminatrice", mais les bornes vérifiées indépendamment (confirmées
    # ci-dessus par le cas d'Anthony) le classent en "Pleine" — voir
    # core.lunation pour la justification détaillée.
    assert result.name == "pleine"
