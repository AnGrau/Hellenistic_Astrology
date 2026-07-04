from hellenistic_astrology.core.sect import is_diurnal, sect_role


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


def test_mercury_always_neutral():
    assert sect_role("Mercure", diurnal_chart=True) == "Neutre"
    assert sect_role("Mercure", diurnal_chart=False) == "Neutre"


def test_benefics_and_malefics():
    assert sect_role("Vénus", diurnal_chart=False) == "Bénéfique de secte"
    assert sect_role("Vénus", diurnal_chart=True) == "Bénéfique hors secte"
    assert sect_role("Jupiter", diurnal_chart=True) == "Bénéfique de secte"
    assert sect_role("Mars", diurnal_chart=False) == "Maléfique de secte"
    assert sect_role("Saturne", diurnal_chart=True) == "Maléfique de secte"
