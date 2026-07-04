from datetime import datetime, timedelta

import pytest

from hellenistic_astrology.core.timezone import resolve_utc
from hellenistic_astrology.core.zodiacal_releasing import (
    SIGN_RULERS,
    ZODIACAL_RELEASING_YEARS,
    ReleasingPeriod,
    active_period,
    angular_signs_from,
    is_peak_period,
    level_periods,
    releasing_tree,
    sub_periods,
)

from .regression_helpers import birth_data_from_fixture, load_fixture


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


# Relâchement du lien ("loosing of the bond") : le signe de destination
# (opposé au signe de départ, pas au dernier signe visité) était un point non
# résolu de "Reste à faire" — tranché par plusieurs sources indépendantes
# (Mountain Astrologer, The Astrology Podcast/lignée Brennan) et confirmé,
# à la date et au signe exacts, par calcul direct sur les deux thèmes de
# référence (non documenté dans les .docx, qui ne couvrent pas cette
# technique — voir CLAUDE.md).
# Un tour complet des 12 signes totalise toujours 211 "années" (somme de
# ZODIACAL_RELEASING_YEARS), quel que soit le signe de départ : à l'unité du
# niveau 2 (mois de 30 jours), cela fait 211*30 = 6330 jours (~17,3 ans).
FULL_CYCLE_UNITS = 211


def test_level_periods_loosing_of_the_bond_jumps_to_opposite_of_start_sign():
    # Verseau (30 ans) : un tour complet des 12 signes (~17,4 ans) tient
    # largement dedans. Après les 12 signes du premier tour (index 0-11), le
    # 13e doit être Lion (opposé de Verseau), pas Verseau lui-même : Verseau
    # ne réapparaît donc jamais deux fois de suite dans la séquence.
    periods = level_periods(
        2, "Verseau", datetime(2000, 1, 1), timedelta(days=(FULL_CYCLE_UNITS + 60) * 30)
    )
    signs = [p.sign for p in periods]
    assert signs[:12] == [
        "Verseau", "Poissons", "Bélier", "Taureau", "Gémeaux", "Cancer",
        "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire", "Capricorne",
    ]
    assert signs[12] == "Lion"
    assert periods[12].bond_loosed is True
    assert "Verseau" not in signs[1:]


def test_level_periods_bond_loosed_flag_only_on_the_jump_period():
    periods = level_periods(
        2, "Verseau", datetime(2000, 1, 1), timedelta(days=(FULL_CYCLE_UNITS + 60) * 30)
    )
    loosed = [p for p in periods if p.bond_loosed]
    assert len(loosed) == 1
    assert loosed[0].sign == "Lion"


def test_level_periods_no_loosing_when_start_sign_never_repeats():
    # Bélier (15 ans) : plus court qu'un tour complet (~17,4 ans), Bélier ne
    # réapparaît jamais -> aucun relâchement du lien.
    periods = level_periods(2, "Bélier", datetime(2000, 1, 1), timedelta(days=15 * 30))
    assert all(not p.bond_loosed for p in periods)
    assert [p.sign for p in periods] == ["Bélier"]


def test_level_periods_loosing_applies_recursively_at_any_level():
    # Même mécanisme, appelé à un niveau plus profond (L3 dans un contexte
    # L2) : pas de code spécifique au niveau, `level_periods` est la même
    # fonction à tous les niveaux. Unité du niveau 3 (2,5 jours) : un tour
    # complet fait 211*2,5 = 527,5 jours.
    periods = level_periods(
        3, "Verseau", datetime(2000, 1, 1), timedelta(days=(FULL_CYCLE_UNITS + 60) * 2.5)
    )
    signs = [p.sign for p in periods]
    assert signs[12] == "Lion"
    assert periods[12].bond_loosed is True


@pytest.mark.parametrize(
    "l1_sign, l1_start, l1_end, expected_jump_date, expected_destination",
    [
        # Anthony, Part de Fortune (Capricorne, non documenté dans le .docx,
        # qui ne détaille pas l'historique de libération zodiacale) :
        # bouclage exact le 30/10/2014, saut vers le Cancer (opposé du
        # Capricorne) — dates et signe confirmés par calcul direct.
        ("Capricorne", datetime(1997, 7, 1), datetime(2024, 2, 10), datetime(2014, 10, 30), "Cancer"),
        # Liam, Part de Fortune (Lion) : bouclage exact le 17/02/2023, saut
        # vers le Verseau (opposé du Lion).
        ("Lion", datetime(2005, 10, 19), datetime(2024, 7, 11), datetime(2023, 2, 17), "Verseau"),
    ],
)
def test_loosing_of_the_bond_reference_charts_fortune(
    l1_sign, l1_start, l1_end, expected_jump_date, expected_destination
):
    parent = ReleasingPeriod(level=1, sign=l1_sign, ruler=SIGN_RULERS[l1_sign], start=l1_start, end=l1_end)
    children = sub_periods(parent)
    loosed = next(p for p in children if p.bond_loosed)
    assert loosed.start == expected_jump_date
    assert loosed.sign == expected_destination


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


# La technique (algorithme, table des années) est la même quelle que soit la
# Part de départ : seule change le signe de départ (Fortune ou Esprit). Les
# tests ci-dessous ancrent explicitement l'usage à partir de la Part de
# l'Esprit sur les deux thèmes de référence, en plus des tests génériques
# ci-dessus qui couvrent déjà l'algorithme pour des signes de départ
# arbitraires — aucune fixture Anthony/Liam ne documente de périodes de
# libération zodiacale attendues (comme pour la Part de Fortune), donc ces
# tests valident le branchement (signe de départ, date de naissance réelle),
# pas des dates de résultat vérifiées indépendamment.
@pytest.mark.parametrize(
    "fixture_name, expected_spirit_sign",
    [("anthony", "Taureau"), ("liam", "Cancer")],
)
def test_l1_from_part_of_spirit_reference_charts(fixture_name, expected_spirit_sign):
    fixture = load_fixture(fixture_name)
    assert fixture["part_of_spirit"]["sign"] == expected_spirit_sign

    birth = birth_data_from_fixture(fixture)
    birth_dt = resolve_utc(birth)
    horizon = birth_dt.replace(year=birth_dt.year + 80)

    periods = releasing_tree(expected_spirit_sign, birth_dt, horizon, max_level=1)

    assert periods[0].sign == expected_spirit_sign
    assert periods[0].start == birth_dt


# Périodes culminantes ("peak periods") : confirmées par une source primaire
# (Chris Brennan, podcast épisode 192) — angulaires (1er/4e/7e/10e) toujours
# par rapport à la Part de Fortune, même en suivant la séquence de l'Esprit.
def test_angular_signs_are_the_same_modality_group():
    # Scorpion (fixe) : les 3 autres signes fixes lui sont angulaires.
    assert angular_signs_from("Scorpion") == {"Scorpion", "Verseau", "Taureau", "Lion"}


def test_angular_signs_include_the_sign_itself():
    assert "Bélier" in angular_signs_from("Bélier")


@pytest.mark.parametrize(
    "fixture_name, expected_fortune_sign",
    [("anthony", "Scorpion"), ("liam", "Lion")],
)
def test_is_peak_period_against_reference_charts_fortune(fixture_name, expected_fortune_sign):
    fixture = load_fixture(fixture_name)
    assert fixture["part_of_fortune"]["sign"] == expected_fortune_sign

    angular = angular_signs_from(expected_fortune_sign)
    for sign in ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"]:
        period = level_periods(1, sign, datetime(2000, 1, 1), timedelta(days=1))[0]
        assert is_peak_period(period, expected_fortune_sign) == (sign in angular)


def test_is_peak_period_reference_stays_fortune_even_when_tracking_spirit():
    # Séquence suivant la Part de l'Esprit (Taureau, Anthony) : les périodes
    # culminantes restent mesurées depuis la Part de Fortune (Scorpion), pas
    # depuis l'Esprit lui-même.
    fortune_sign = "Scorpion"
    spirit_start = "Taureau"
    periods = releasing_tree(spirit_start, datetime(2000, 1, 1), datetime(2010, 1, 1), max_level=1)
    assert is_peak_period(periods[0], fortune_sign) is True  # Taureau est angulaire à Scorpion (fixe)
