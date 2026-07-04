import pytest

from hellenistic_astrology.core.dignities import (
    EGYPTIAN_BOUNDS,
    bound_dignity,
    egyptian_bound_ruler,
    essential_dignity,
    mutual_receptions_by_domicile,
    traditional_rulerships,
    triplicity_dignity,
)


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


def test_mutual_reception_by_domicile_detected():
    # Anthony : Mars (Balance, domicile de Vénus) / Vénus (Scorpion, domicile de Mars).
    positions = {"Vénus": "Scorpion", "Mars": "Balance"}
    receptions = mutual_receptions_by_domicile(positions)
    assert len(receptions) == 1
    assert receptions[0].planet_a == "Vénus"
    assert receptions[0].planet_b == "Mars"


def test_mutual_reception_requires_both_directions():
    # Mars en Scorpion (son propre domicile) et Soleil en Lion (son propre
    # domicile) : chacun chez soi, mais aucun n'est dans le domicile de l'autre.
    positions = {"Soleil": "Lion", "Mars": "Scorpion"}
    assert mutual_receptions_by_domicile(positions) == []


def test_mutual_reception_one_directional_does_not_count():
    # Mars en Balance (domicile de Vénus), mais Vénus en Gémeaux (pas un
    # domicile de Mars) -> une seule direction, donc pas de réception mutuelle.
    positions = {"Vénus": "Gémeaux", "Mars": "Balance"}
    assert mutual_receptions_by_domicile(positions) == []


def test_mutual_reception_none_when_no_match():
    positions = {"Soleil": "Bélier", "Lune": "Gémeaux"}
    assert mutual_receptions_by_domicile(positions) == []


def test_triplicity_fire_rulers():
    assert triplicity_dignity("Soleil", "Bélier") == "Maître de triplicité (jour)"
    assert triplicity_dignity("Jupiter", "Lion") == "Maître de triplicité (nuit)"
    assert triplicity_dignity("Saturne", "Sagittaire") == "Maître de triplicité (participant)"


def test_triplicity_earth_rulers():
    assert triplicity_dignity("Vénus", "Taureau") == "Maître de triplicité (jour)"
    assert triplicity_dignity("Lune", "Vierge") == "Maître de triplicité (nuit)"
    assert triplicity_dignity("Mars", "Capricorne") == "Maître de triplicité (participant)"


def test_triplicity_air_rulers():
    assert triplicity_dignity("Saturne", "Gémeaux") == "Maître de triplicité (jour)"
    assert triplicity_dignity("Mercure", "Balance") == "Maître de triplicité (nuit)"
    assert triplicity_dignity("Jupiter", "Verseau") == "Maître de triplicité (participant)"


def test_triplicity_water_rulers():
    # Système dorothéen (Vénus/Mars/Lune) — pas le système ptoléméen
    # simplifié (Mars jour et nuit, sans participant).
    assert triplicity_dignity("Vénus", "Cancer") == "Maître de triplicité (jour)"
    assert triplicity_dignity("Mars", "Scorpion") == "Maître de triplicité (nuit)"
    assert triplicity_dignity("Lune", "Poissons") == "Maître de triplicité (participant)"


def test_triplicity_none_when_not_a_ruler():
    assert triplicity_dignity("Mercure", "Bélier") is None


def test_egyptian_bounds_each_sign_totals_30_degrees():
    for sign, segments in EGYPTIAN_BOUNDS.items():
        assert segments[-1][0] == 30, f"{sign} ne totalise pas 30°"
        previous = 0
        for upper_bound, _ruler in segments:
            assert upper_bound > previous, f"{sign} : bornes non strictement croissantes"
            previous = upper_bound


def test_egyptian_bound_ruler_aries_boundaries():
    # Bélier : Jupiter 0-6, Vénus 6-12, Mercure 12-20, Mars 20-25, Saturne 25-30.
    assert egyptian_bound_ruler("Bélier", 0) == "Jupiter"
    assert egyptian_bound_ruler("Bélier", 5.9999) == "Jupiter"
    assert egyptian_bound_ruler("Bélier", 6) == "Vénus"
    assert egyptian_bound_ruler("Bélier", 19.9999) == "Mercure"
    assert egyptian_bound_ruler("Bélier", 20) == "Mars"
    assert egyptian_bound_ruler("Bélier", 29.9999) == "Saturne"


def test_egyptian_bound_ruler_aquarius_boundaries():
    # Verseau : Mercure 0-7, Vénus 7-13, Jupiter 13-20, Mars 20-25, Saturne 25-30.
    assert egyptian_bound_ruler("Verseau", 0) == "Mercure"
    assert egyptian_bound_ruler("Verseau", 7) == "Vénus"
    assert egyptian_bound_ruler("Verseau", 13) == "Jupiter"
    assert egyptian_bound_ruler("Verseau", 20) == "Mars"
    assert egyptian_bound_ruler("Verseau", 25) == "Saturne"


def test_egyptian_bound_ruler_rejects_out_of_range_degree():
    with pytest.raises(ValueError):
        egyptian_bound_ruler("Bélier", 30)
    with pytest.raises(ValueError):
        egyptian_bound_ruler("Bélier", -1)


def test_bound_dignity_when_planet_is_its_own_bound_ruler():
    assert bound_dignity("Jupiter", "Bélier", 3) == "Maître du terme (bornes égyptiennes)"


def test_bound_dignity_none_when_not_ruler():
    assert bound_dignity("Mars", "Bélier", 3) is None
