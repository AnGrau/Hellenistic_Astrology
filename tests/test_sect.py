import pytest

from hellenistic_astrology.core.sect import is_diurnal, mercury_is_morning_star, sect_role


def test_is_diurnal():
    assert is_diurnal(7) is True
    assert is_diurnal(12) is True
    assert is_diurnal(1) is False
    assert is_diurnal(6) is False


def test_luminaries_symmetric_out_of_sect():
    assert sect_role("Soleil", diurnal_chart=False) == "Hors secte (nuit)"
    assert sect_role("Lune", diurnal_chart=True) == "Hors secte (jour)"
    assert sect_role("Soleil", diurnal_chart=True) == "Lumière de secte"
    assert sect_role("Lune", diurnal_chart=False) == "Lumière de secte"


def test_mercury_is_morning_star():
    # Mercure derrière le Soleil (longitude moindre) : étoile du matin.
    assert mercury_is_morning_star(mercury_longitude=10.0, sun_longitude=20.0) is True
    # Mercure devant le Soleil (longitude supérieure) : étoile du soir.
    assert mercury_is_morning_star(mercury_longitude=30.0, sun_longitude=20.0) is False
    # Enroulement autour de 0°/360° : Mercure à 355°, Soleil à 5° — Mercure
    # est en réalité juste derrière le Soleil (10° d'écart réel), donc
    # étoile du matin, pas l'inverse qu'une soustraction naïve suggérerait.
    assert mercury_is_morning_star(mercury_longitude=355.0, sun_longitude=5.0) is True
    assert mercury_is_morning_star(mercury_longitude=5.0, sun_longitude=355.0) is False


def test_mercury_sect_role_depends_on_phase():
    # Étoile du matin => affinité diurne : en secte dans un thème de jour,
    # hors secte dans un thème de nuit (symétrique à Jupiter/Saturne).
    assert sect_role("Mercure", diurnal_chart=True, mercury_morning_star=True) == "Neutre de secte"
    assert sect_role("Mercure", diurnal_chart=False, mercury_morning_star=True) == "Neutre hors secte"
    # Étoile du soir => affinité nocturne : en secte de nuit, hors secte de jour.
    assert sect_role("Mercure", diurnal_chart=False, mercury_morning_star=False) == "Neutre de secte"
    assert sect_role("Mercure", diurnal_chart=True, mercury_morning_star=False) == "Neutre hors secte"


def test_mercury_sect_role_requires_phase_argument():
    with pytest.raises(ValueError):
        sect_role("Mercure", diurnal_chart=True)


def test_benefics_and_malefics():
    assert sect_role("Vénus", diurnal_chart=False) == "Bénéfique de secte"
    assert sect_role("Vénus", diurnal_chart=True) == "Bénéfique hors secte"
    assert sect_role("Jupiter", diurnal_chart=True) == "Bénéfique de secte"
    assert sect_role("Mars", diurnal_chart=False) == "Maléfique de secte"
    assert sect_role("Saturne", diurnal_chart=True) == "Maléfique de secte"
