from datetime import datetime, timedelta

import pytest

from hellenistic_astrology.core.zodiacal_releasing import (
    SIGN_RULERS,
    ZODIACAL_RELEASING_YEARS,
    active_period,
    level_periods,
    releasing_tree,
    sub_periods,
)


def test_years_table_has_all_signs():
    assert set(ZODIACAL_RELEASING_YEARS) == {
        "Bélier",
        "Taureau",
        "Gémeaux",
        "Cancer",
        "Lion",
        "Vierge",
        "Balance",
        "Scorpion",
        "Sagittaire",
        "Capricorne",
        "Verseau",
        "Poissons",
    }


def test_capricorn_and_aquarius_differ_despite_shared_ruler():
    # Particularité documentée de la technique (Valens) : les deux domiciles
    # de Saturne n'ont pas la même durée en libération zodiacale.
    assert ZODIACAL_RELEASING_YEARS["Capricorne"] == 27
    assert ZODIACAL_RELEASING_YEARS["Verseau"] == 30


def test_sign_rulers_match_domiciles():
    assert SIGN_RULERS["Lion"] == "Soleil"
    assert SIGN_RULERS["Cancer"] == "Lune"
    assert SIGN_RULERS["Capricorne"] == "Saturne"
    assert SIGN_RULERS["Verseau"] == "Saturne"


def test_l1_brennan_worked_example_cancer_to_leo():
    # Exemple chiffré tiré directement de la transcription du podcast de
    # Chris Brennan (épisode 192) : une période de niveau 1 en Cancer (25 ans)
    # débutant le 1/1/2012 se termine le 22/8/2036, parce que la technique
    # utilise des années de 360 jours (et non l'année solaire de 365,25 jours).
    start = datetime(2012, 1, 1)
    periods = level_periods(1, "Cancer", start, timedelta(days=25 * 360))
    assert len(periods) == 1
    assert periods[0].sign == "Cancer"
    assert periods[0].end == datetime(2036, 8, 22)


def test_l1_sequence_advances_through_signs_in_order():
    start = datetime(2000, 1, 1)
    periods = level_periods(1, "Lion", start, timedelta(days=(19 + 20 + 8) * 360))
    assert [p.sign for p in periods] == ["Lion", "Vierge", "Balance"]
    assert periods[0].end == periods[1].start
    assert periods[1].end == periods[2].start


def test_level_periods_partition_exactly_the_given_duration():
    start = datetime(1990, 5, 15, 12, 30)
    duration = timedelta(days=12345)
    for start_sign in ["Bélier", "Cancer", "Verseau"]:
        for level in [1, 2, 3, 4]:
            periods = level_periods(level, start_sign, start, duration)
            assert periods[0].start == start
            assert periods[-1].end == start + duration
            for a, b in zip(periods, periods[1:]):
                assert a.end == b.start


def test_sub_periods_start_with_same_sign_as_parent():
    # "the first level two within that level one will always be the same
    # sign" (Chris Brennan, podcast épisode 192).
    parent = level_periods(1, "Cancer", datetime(2000, 1, 1), timedelta(days=25 * 360))[0]
    children = sub_periods(parent)
    assert children[0].sign == "Cancer"
    assert children[0].start == parent.start


def test_sub_periods_partition_parent_exactly():
    parent = level_periods(1, "Verseau", datetime(2000, 1, 1), timedelta(days=30 * 360))[0]
    children = sub_periods(parent)
    assert children[0].start == parent.start
    assert children[-1].end == parent.end
    for a, b in zip(children, children[1:]):
        assert a.end == b.start


def test_sub_periods_wrap_around_the_zodiac_more_than_once():
    # Un tour complet des 12 signes (au niveau 2, en mois de 30 jours) totalise
    # 211 mois = 6330 jours, largement inférieur à une période Verseau de
    # niveau 1 (30 ans = 10800 jours) : le signe de départ doit donc réapparaître.
    parent = level_periods(1, "Verseau", datetime(2000, 1, 1), timedelta(days=30 * 360))[0]
    children = sub_periods(parent)
    signs_seen = [c.sign for c in children]
    assert signs_seen.count("Verseau") >= 2


def test_sub_periods_of_level_4_raises():
    parent = level_periods(4, "Bélier", datetime(2000, 1, 1), timedelta(days=1))[0]
    with pytest.raises(ValueError):
        sub_periods(parent)


def test_releasing_tree_respects_max_level():
    birth = datetime(2000, 1, 1)
    horizon = datetime(2010, 1, 1)
    tree = releasing_tree("Lion", birth, horizon, max_level=2)
    levels_present = {p.level for p in tree}
    assert levels_present == {1, 2}


def test_releasing_tree_l1_truncated_at_horizon():
    birth = datetime(2000, 1, 1)
    horizon = datetime(2005, 1, 1)
    tree = releasing_tree("Lion", birth, horizon, max_level=1)
    assert tree[-1].end == horizon


def test_active_period_finds_containing_period():
    birth = datetime(2000, 1, 1)
    horizon = datetime(2050, 1, 1)
    tree = releasing_tree("Lion", birth, horizon, max_level=1)
    active = active_period(tree, 1, datetime(2001, 6, 1))
    assert active is not None
    assert active.sign == "Lion"


def test_active_period_returns_none_outside_range():
    birth = datetime(2000, 1, 1)
    horizon = datetime(2010, 1, 1)
    tree = releasing_tree("Lion", birth, horizon, max_level=1)
    assert active_period(tree, 1, datetime(1999, 1, 1)) is None
