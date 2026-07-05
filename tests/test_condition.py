import pytest

from hellenistic_astrology.core import condition
from hellenistic_astrology.core.condition import (
    AspectInfluence,
    _bonification_corruption,
    _closest_to_sign_boundary,
    _configuration_score,
    _enclosure,
    _moon_applies_to,
    _solar_phenomenon_tier,
    compute_planetary_conditions,
)
from hellenistic_astrology.core.dignities import MutualReception, SolarProximity
from hellenistic_astrology.core.observation import PointPosition
from hellenistic_astrology.core.sect import sect_role


def _point(name: str, sign: str, degree_in_sign: float = 15.0, **kwargs) -> PointPosition:
    return PointPosition(name=name, sign=sign, degree_in_sign=degree_in_sign, house=1, **kwargs)


# ---------------------------------------------------------------------------
# Bonification / corruption
# ---------------------------------------------------------------------------


def test_benefic_trigone_and_sextile_aid():
    mars = _point("Mars", "Bélier")
    jupiter_trigone = _point("Jupiter", "Lion")  # distance 4 -> Trigone
    venus_sextile = _point("Vénus", "Gémeaux")  # distance 2 -> Sextile
    bc = _bonification_corruption(mars, [jupiter_trigone, venus_sextile])
    assert set(bc.aided_by) == {
        AspectInfluence(source="Jupiter", aspect="Trigone"),
        AspectInfluence(source="Vénus", aspect="Sextile"),
    }
    assert bc.harmed_by == ()


def test_benefic_square_or_opposition_has_no_effect():
    mars = _point("Mars", "Bélier")
    venus_square = _point("Vénus", "Cancer")  # distance 3 -> Carré
    jupiter_opposition = _point("Jupiter", "Balance")  # distance 6 -> Opposition
    bc = _bonification_corruption(mars, [venus_square, jupiter_opposition])
    assert bc.aided_by == ()
    assert bc.harmed_by == ()


def test_malefic_square_and_opposition_harm():
    mercure = _point("Mercure", "Bélier")
    saturne_carre = _point("Saturne", "Cancer")  # distance 3 -> Carré
    mars_opposition = _point("Mars", "Balance")  # distance 6 -> Opposition
    bc = _bonification_corruption(mercure, [saturne_carre, mars_opposition])
    assert set(bc.harmed_by) == {
        AspectInfluence(source="Saturne", aspect="Carré"),
        AspectInfluence(source="Mars", aspect="Opposition"),
    }
    assert bc.aided_by == ()


def test_malefic_trigone_or_sextile_has_no_effect():
    mercure = _point("Mercure", "Bélier")
    mars_trigone = _point("Mars", "Lion")  # distance 4 -> Trigone
    saturne_sextile = _point("Saturne", "Gémeaux")  # distance 2 -> Sextile
    bc = _bonification_corruption(mercure, [mars_trigone, saturne_sextile])
    assert bc.aided_by == ()
    assert bc.harmed_by == ()


def test_conjunction_aids_or_harms_depending_on_nature():
    mercure = _point("Mercure", "Bélier")
    venus_conjunction = _point("Vénus", "Bélier")
    mars_conjunction = _point("Mars", "Bélier")
    bc = _bonification_corruption(mercure, [venus_conjunction, mars_conjunction])
    assert bc.aided_by == (AspectInfluence(source="Vénus", aspect="Conjonction"),)
    assert bc.harmed_by == (AspectInfluence(source="Mars", aspect="Conjonction"),)


def test_planet_never_aids_or_harms_itself():
    venus = _point("Vénus", "Bélier")
    # Se glisse par erreur dans sa propre liste "others" : doit être ignorée.
    bc = _bonification_corruption(venus, [venus])
    assert bc.aided_by == ()
    assert bc.harmed_by == ()


def test_planet_can_be_both_aided_and_harmed_simultaneously():
    mercure = _point("Mercure", "Bélier")
    jupiter_trigone = _point("Jupiter", "Lion")
    saturne_carre = _point("Saturne", "Cancer")
    bc = _bonification_corruption(mercure, [jupiter_trigone, saturne_carre])
    assert bc.aided_by == (AspectInfluence(source="Jupiter", aspect="Trigone"),)
    assert bc.harmed_by == (AspectInfluence(source="Saturne", aspect="Carré"),)


# ---------------------------------------------------------------------------
# Enclosure par signe
# ---------------------------------------------------------------------------


def test_enclosure_benefic_both_sides():
    # Cancer encadré par Gémeaux (fin, proche de la frontière) et Lion (début).
    planet = _point("Mars", "Cancer", degree_in_sign=15.0)
    venus_before = _point("Vénus", "Gémeaux", degree_in_sign=27.0)  # à 3° de la fin
    jupiter_after = _point("Jupiter", "Lion", degree_in_sign=2.0)  # à 2° du début
    planets_by_name = {p.name: p for p in (planet, venus_before, jupiter_after)}
    enc = _enclosure(planet, planets_by_name)
    assert enc.category == "bénéfique"
    assert enc.flanking_planets == ("Vénus", "Jupiter")


def test_enclosure_malefic_both_sides_is_besiegement():
    planet = _point("Vénus", "Cancer", degree_in_sign=15.0)
    mars_before = _point("Mars", "Gémeaux", degree_in_sign=25.0)
    saturne_after = _point("Saturne", "Lion", degree_in_sign=6.9)
    planets_by_name = {p.name: p for p in (planet, mars_before, saturne_after)}
    enc = _enclosure(planet, planets_by_name)
    assert enc.category == "maléfique"
    assert enc.flanking_planets == ("Mars", "Saturne")


def test_enclosure_mixed_nature_records_flanking_but_no_category():
    planet = _point("Mercure", "Cancer", degree_in_sign=15.0)
    venus_before = _point("Vénus", "Gémeaux", degree_in_sign=28.0)
    saturne_after = _point("Saturne", "Lion", degree_in_sign=1.0)
    planets_by_name = {p.name: p for p in (planet, venus_before, saturne_after)}
    enc = _enclosure(planet, planets_by_name)
    assert enc.category is None
    assert enc.flanking_planets == ("Vénus", "Saturne")


def test_enclosure_requires_both_sides_occupied():
    planet = _point("Mercure", "Cancer", degree_in_sign=15.0)
    only_before = _point("Vénus", "Gémeaux", degree_in_sign=28.0)
    planets_by_name = {p.name: p for p in (planet, only_before)}
    enc = _enclosure(planet, planets_by_name)
    assert enc.category is None
    assert enc.flanking_planets is None


def test_closest_to_sign_boundary_threshold_excludes_at_exactly_7_degrees():
    planets_by_name = {
        "Vénus": _point("Vénus", "Gémeaux", degree_in_sign=23.0),  # exactement à 7° de la fin (30-23=7)
    }
    assert _closest_to_sign_boundary("Gémeaux", near_end=True, planets_by_name=planets_by_name, exclude="X") is None
    planets_by_name["Vénus"] = _point("Vénus", "Gémeaux", degree_in_sign=23.01)  # juste en dessous de 7°
    result = _closest_to_sign_boundary("Gémeaux", near_end=True, planets_by_name=planets_by_name, exclude="X")
    assert result is not None and result.name == "Vénus"


def test_closest_to_sign_boundary_picks_nearest_candidate():
    planets_by_name = {
        "Vénus": _point("Vénus", "Gémeaux", degree_in_sign=25.0),  # à 5° de la fin
        "Jupiter": _point("Jupiter", "Gémeaux", degree_in_sign=29.0),  # à 1° de la fin
    }
    result = _closest_to_sign_boundary("Gémeaux", near_end=True, planets_by_name=planets_by_name, exclude="X")
    assert result is not None and result.name == "Jupiter"


# ---------------------------------------------------------------------------
# Phénomènes solaires imbriqués
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "gap_degrees,expected_tier",
    [
        (0.5, "Cazimi"),
        (0.999, "Cazimi"),
        (1.0, "Combustion"),
        (5.0, "Combustion"),
        (8.999, "Combustion"),
        (9.0, "Sous les rayons"),
        (12.0, "Sous les rayons"),
        (14.999, "Sous les rayons"),
        (15.0, None),
        (20.0, None),
    ],
)
def test_solar_phenomenon_tier_boundaries(gap_degrees, expected_tier):
    tier = _solar_phenomenon_tier("Mercure", gap_degrees, essential_dignity="Pérégrin")
    assert tier.tier == expected_tier


def test_solar_phenomenon_resists_via_dignity_flag():
    assert _solar_phenomenon_tier("Mercure", 5.0, essential_dignity="Domicile").resists_via_dignity is True
    assert _solar_phenomenon_tier("Mercure", 5.0, essential_dignity="Exaltation").resists_via_dignity is True
    assert _solar_phenomenon_tier("Mercure", 5.0, essential_dignity="Pérégrin").resists_via_dignity is False
    assert _solar_phenomenon_tier("Mercure", 5.0, essential_dignity="Exil (détriment)").resists_via_dignity is False


# ---------------------------------------------------------------------------
# Application de la Lune
# ---------------------------------------------------------------------------


def test_moon_applies_via_conjunction():
    # Lune plus rapide (13°/j) que Mercure (1°/j), derrière lui dans le même
    # signe : l'écart se resserre, application vraie.
    moon = _point("Lune", "Bélier", degree_in_sign=10.0, speed=13.0)
    mercure = _point("Mercure", "Bélier", degree_in_sign=12.0, speed=1.0)
    assert _moon_applies_to(moon, mercure) is True


def test_moon_does_not_apply_when_separating():
    # Lune déjà passée devant Mercure (écart qui s'élargit).
    moon = _point("Lune", "Bélier", degree_in_sign=15.0, speed=13.0)
    mercure = _point("Mercure", "Bélier", degree_in_sign=12.0, speed=1.0)
    assert _moon_applies_to(moon, mercure) is False


def test_moon_never_applies_to_itself():
    moon = _point("Lune", "Bélier", degree_in_sign=10.0, speed=13.0)
    assert _moon_applies_to(moon, moon) is False


def test_moon_does_not_apply_across_an_aversion():
    moon = _point("Lune", "Bélier", degree_in_sign=10.0, speed=13.0)
    mercure = _point("Mercure", "Taureau", degree_in_sign=1.0, speed=1.0)  # distance 1 -> Aversion
    assert _moon_applies_to(moon, mercure) is False


# ---------------------------------------------------------------------------
# Secte : couverture complète des 9 sorties possibles de sect_role()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "planet,diurnal_chart,mercury_morning_star",
    [
        ("Soleil", True, None),
        ("Soleil", False, None),
        ("Lune", True, None),
        ("Lune", False, None),
        ("Vénus", True, None),
        ("Vénus", False, None),
        ("Jupiter", True, None),
        ("Jupiter", False, None),
        ("Mars", True, None),
        ("Mars", False, None),
        ("Saturne", True, None),
        ("Saturne", False, None),
        ("Mercure", True, True),
        ("Mercure", True, False),
        ("Mercure", False, True),
        ("Mercure", False, False),
    ],
)
def test_sect_role_rank_covers_every_possible_output(planet, diurnal_chart, mercury_morning_star):
    role = sect_role(planet, diurnal_chart, mercury_morning_star=mercury_morning_star)
    assert role in condition.SECT_ROLE_RANK


def test_sect_role_rank_has_exactly_nine_entries():
    assert len(condition.SECT_ROLE_RANK) == 9


# ---------------------------------------------------------------------------
# Configuration score (niveau 6)
# ---------------------------------------------------------------------------


def test_configuration_score_favors_aid_and_benefic_enclosure():
    bc = condition.BonificationCorruption(
        planet="Mercure", aided_by=(AspectInfluence(source="Vénus", aspect="Trigone"),), harmed_by=()
    )
    enc_benefic = condition.Enclosure(planet="Mercure", flanking_planets=("Vénus", "Jupiter"), category="bénéfique")
    enc_none = condition.Enclosure(planet="Mercure")
    assert _configuration_score(bc, enc_benefic) < _configuration_score(bc, enc_none)


def test_configuration_score_penalizes_harm_and_malefic_enclosure():
    bc = condition.BonificationCorruption(
        planet="Mercure", aided_by=(), harmed_by=(AspectInfluence(source="Mars", aspect="Carré"),)
    )
    enc_malefic = condition.Enclosure(planet="Mercure", flanking_planets=("Mars", "Saturne"), category="maléfique")
    enc_none = condition.Enclosure(planet="Mercure")
    assert _configuration_score(bc, enc_malefic) > _configuration_score(bc, enc_none)


# ---------------------------------------------------------------------------
# Classement complet (compute_planetary_conditions)
# ---------------------------------------------------------------------------


def _classical_seven() -> list[PointPosition]:
    """Sept planètes classiques synthétiques, signes mutuellement en
    aversion entre elles par défaut (pas de bonification/corruption
    accidentelle) sauf celles délibérément construites dans le test qui
    consomme cette fixture. Champs de dignité/secte/angularité neutres par
    défaut, à écraser au cas par cas."""
    return [
        _point("Soleil", "Bélier", 10.0, essential_dignity="Pérégrin", sect_role="Hors secte (nuit)",
               house_quality="Cadente", speed=1.0),
        _point("Lune", "Taureau", 10.0, essential_dignity="Pérégrine", sect_role="Hors secte (jour)",
               house_quality="Cadente", speed=13.0),
        _point("Mercure", "Vierge", 10.0, essential_dignity="Domicile", sect_role="Neutre de secte",
               house_quality="Angulaire", speed=1.0),
        _point("Vénus", "Cancer", 10.0, essential_dignity="Pérégrine", sect_role="Bénéfique de secte",
               house_quality="Succédente", speed=1.0),
        _point("Mars", "Poissons", 10.0, essential_dignity="Chute", sect_role="Maléfique hors secte",
               house_quality="Cadente", speed=0.3),
        _point("Jupiter", "Taureau", 20.0, essential_dignity="Pérégrin", sect_role="Bénéfique hors secte",
               house_quality="Succédente", speed=0.2),
        _point("Saturne", "Sagittaire", 10.0, essential_dignity="Pérégrin", sect_role="Maléfique de secte",
               house_quality="Cadente", speed=0.05),
    ]


def test_full_ranking_is_a_permutation_of_1_to_7():
    planets = _classical_seven()
    conditions = compute_planetary_conditions(planets, mutual_receptions=[], solar_proximity=[])
    assert sorted(c.rank for c in conditions) == [1, 2, 3, 4, 5, 6, 7]


def test_full_ranking_preserves_input_order_not_rank_order():
    planets = _classical_seven()
    conditions = compute_planetary_conditions(planets, mutual_receptions=[], solar_proximity=[])
    assert [c.planet for c in conditions] == [p.name for p in planets]


def test_configuration_advantage_never_overrides_earlier_levels():
    # Mercure : excellent aux niveaux 1-3 (secte neutre de secte, domicile,
    # angulaire) mais harcelé par Saturne (Cancer/Vierge = Carré, distance
    # 3) sans aucune aide. Mars : très mauvais aux niveaux 1-3 (maléfique
    # hors secte, chute, cadent) mais aidé par Vénus (Poissons/Cancer =
    # Trigone, distance 4) et Jupiter (Poissons/Taureau = Sextile, distance
    # 2), sans aucun tort. La construction garantit Mars meilleur que
    # Mercure au niveau 6 (vérifié explicitement ci-dessous) — le test
    # prouve que Mercure l'emporte quand même au classement final, preuve
    # du comportement lexicographique (pas additif).
    planets = _classical_seven()
    conditions = {c.planet: c for c in compute_planetary_conditions(planets, mutual_receptions=[], solar_proximity=[])}

    mercure, mars = conditions["Mercure"], conditions["Mars"]
    # Niveau 6 (configuration_rank) : Mars doit être strictement meilleur
    # (plus bas) que Mercure pour que le test soit probant.
    assert mars.sort_key[5] < mercure.sort_key[5]
    # Niveaux 1-3 : Mercure doit être strictement meilleur que Mars.
    assert mercure.sort_key[0] < mars.sort_key[0]  # secte
    assert mercure.sort_key[1] < mars.sort_key[1]  # dignité
    assert mercure.sort_key[2] < mars.sort_key[2]  # angularité
    # Malgré son désavantage de niveau 6, Mercure surclasse Mars au global.
    assert mercure.rank < mars.rank


def test_deterministic_tie_break_for_otherwise_equal_planets():
    # Mercure et Vénus construits pour être rigoureusement à égalité sur
    # les 6 premiers niveaux (mêmes valeurs partout, aucune relation
    # d'aspect entre eux ni avec le reste) : seul le palier 7 (ordre fixe
    # de CLASSICAL_PLANETS) doit les départager. Mercure précède Vénus dans
    # cet ordre -> doit obtenir le meilleur rang des deux.
    common = dict(essential_dignity="Pérégrin", sect_role="Neutre hors secte", house_quality="Cadente", speed=1.0)
    mercure = _point("Mercure", "Bélier", 10.0, **common)
    # Taureau est en aversion avec Bélier (distance 1) : évite toute
    # bonification croisée entre Mercure et Vénus qui fausserait le niveau 6.
    venus = _point("Vénus", "Taureau", 10.0, **common)
    others = [
        _point("Soleil", "Cancer", 10.0, essential_dignity="Pérégrin", sect_role="Hors secte (nuit)",
               house_quality="Cadente", speed=1.0),
        _point("Lune", "Lion", 10.0, essential_dignity="Pérégrine", sect_role="Hors secte (jour)",
               house_quality="Cadente", speed=13.0),
        _point("Mars", "Vierge", 10.0, essential_dignity="Pérégrin", sect_role="Maléfique hors secte",
               house_quality="Cadente", speed=0.3),
        _point("Jupiter", "Balance", 10.0, essential_dignity="Pérégrin", sect_role="Bénéfique hors secte",
               house_quality="Cadente", speed=0.2),
        # Sagittaire : Trigone avec Bélier (Mercure, malefic-trigone ne
        # compte pas) et Aversion avec Taureau (Vénus) — neutre pour les deux.
        _point("Saturne", "Sagittaire", 10.0, essential_dignity="Pérégrin", sect_role="Maléfique hors secte",
               house_quality="Cadente", speed=0.05),
    ]
    planets = [mercure, venus, *others]
    conditions = {c.planet: c for c in compute_planetary_conditions(planets, mutual_receptions=[], solar_proximity=[])}
    assert conditions["Mercure"].sort_key[:6] == conditions["Vénus"].sort_key[:6]
    assert conditions["Mercure"].rank < conditions["Vénus"].rank


def test_mutual_reception_improves_dignity_rank_within_same_major_tier():
    base = dict(essential_dignity="Pérégrin", sect_role="Neutre hors secte", house_quality="Cadente", speed=1.0)
    with_reception = _point("Mercure", "Bélier", 10.0, **base)
    without_reception = _point("Mercure", "Bélier", 10.0, **base)
    receptions = [MutualReception(planet_a="Mercure", planet_b="Vénus")]
    conditions_with = compute_planetary_conditions([with_reception], mutual_receptions=receptions, solar_proximity=[])
    conditions_without = compute_planetary_conditions([without_reception], mutual_receptions=[], solar_proximity=[])
    assert conditions_with[0].sort_key[1] < conditions_without[0].sort_key[1]


def test_solar_proximity_feeds_into_ranking():
    planet = _point("Mercure", "Bélier", 10.0, essential_dignity="Pérégrin", sect_role="Neutre hors secte",
                     house_quality="Cadente", speed=1.0)
    cazimi = [SolarProximity(planet="Mercure", gap_degrees=0.5)]
    combust = [SolarProximity(planet="Mercure", gap_degrees=5.0)]
    conditions_cazimi = compute_planetary_conditions([planet], mutual_receptions=[], solar_proximity=cazimi)
    conditions_combust = compute_planetary_conditions([planet], mutual_receptions=[], solar_proximity=combust)
    assert conditions_cazimi[0].solar_phenomenon.tier == "Cazimi"
    assert conditions_combust[0].solar_phenomenon.tier == "Combustion"
    assert conditions_cazimi[0].sort_key[3] < conditions_combust[0].sort_key[3]


def test_sun_and_moon_have_no_solar_phenomenon():
    planets = _classical_seven()
    conditions = {c.planet: c for c in compute_planetary_conditions(planets, mutual_receptions=[], solar_proximity=[])}
    assert conditions["Soleil"].solar_phenomenon is None
    assert conditions["Lune"].solar_phenomenon is None
