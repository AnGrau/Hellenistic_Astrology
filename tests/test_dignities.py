from hellenistic_astrology.core.dignities import essential_dignity, traditional_rulerships


def test_domicile():
    assert essential_dignity("Soleil", "Lion") == "Domicile"
    assert essential_dignity("Mars", "Scorpion") == "Domicile"


def test_exaltation():
    assert essential_dignity("Lune", "Taureau") == "Exaltation"


def test_detriment():
    assert essential_dignity("Saturne", "Lion") == "Exil (détriment)"


def test_fall():
    assert essential_dignity("Soleil", "Balance") == "Chute"


def test_peregrine_gender_agreement():
    assert essential_dignity("Soleil", "Scorpion") == "Pérégrin"
    assert essential_dignity("Vénus", "Sagittaire") == "Pérégrine"


def test_traditional_rulerships_from_ascendant():
    # Ascendant Lion (0° Lion = longitude 120).
    rulerships = {r.planet: r for r in traditional_rulerships(120.0)}
    assert rulerships["Mercure"].domicile_signs == ("Gémeaux", "Vierge")
    assert rulerships["Mercure"].houses_governed == (11, 2)
