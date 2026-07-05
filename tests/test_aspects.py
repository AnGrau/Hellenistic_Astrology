from hellenistic_astrology.core.aspects import (
    build_clusters,
    compute_cluster_aspects,
    is_west_of_sun,
    out_of_sign_conjunction,
    sign_aspect,
)
from hellenistic_astrology.core.observation import PointPosition


def test_is_west_of_sun():
    # Généralise mercury_is_morning_star (jalon 38) : mêmes cas, mêmes
    # attentes, pour une planète quelconque.
    assert is_west_of_sun(planet_longitude=10.0, sun_longitude=20.0) is True
    assert is_west_of_sun(planet_longitude=30.0, sun_longitude=20.0) is False
    # Enroulement 0°/360°.
    assert is_west_of_sun(planet_longitude=355.0, sun_longitude=5.0) is True
    assert is_west_of_sun(planet_longitude=5.0, sun_longitude=355.0) is False


def test_sign_aspect_table():
    assert sign_aspect("Bélier", "Bélier") is None
    assert sign_aspect("Bélier", "Gémeaux") == "Sextile"
    assert sign_aspect("Bélier", "Cancer") == "Carré"
    assert sign_aspect("Bélier", "Lion") == "Trigone"
    assert sign_aspect("Bélier", "Balance") == "Opposition"
    assert sign_aspect("Bélier", "Taureau") == "Aversion"
    assert sign_aspect("Bélier", "Vierge") == "Aversion"
    # Symétrique quel que soit le sens.
    assert sign_aspect("Cancer", "Bélier") == "Carré"


def test_build_clusters_groups_by_sign_and_sorts_by_zodiac_order():
    points = [
        PointPosition(name="Ascendant", sign="Lion", degree_in_sign=10, house=1),
        PointPosition(name="Lune", sign="Lion", degree_in_sign=20, house=1),
        PointPosition(name="Soleil", sign="Bélier", degree_in_sign=5, house=9),
    ]
    clusters = build_clusters(points)
    assert [c.sign for c in clusters] == ["Bélier", "Lion"]
    assert clusters[1].members == ("Ascendant", "Lune")
    assert clusters[1].house == 1


def test_out_of_sign_conjunction_not_triggered_when_far_from_boundary():
    # Cas Anthony : Mercure (Sagittaire 11°57') / Vénus (Scorpion 11°51') —
    # degrés-dans-signe proches par coïncidence, mais ~30° d'écart réel.
    mercury = PointPosition(name="Mercure", sign="Sagittaire", degree_in_sign=11.95, house=5, speed=1.2)
    venus = PointPosition(name="Vénus", sign="Scorpion", degree_in_sign=11.85, house=4, speed=-0.3)
    assert out_of_sign_conjunction(mercury, venus) is False


def test_out_of_sign_conjunction_triggers_near_boundary_when_applying():
    # Cas synthétique (absent des deux thèmes de référence) : planète rapide
    # à 28°30' d'un signe, appliquant vers une planète lente à 0°30' du
    # signe suivant (écart réel de 2°, la plus rapide se rapproche).
    fast = PointPosition(name="Lune", sign="Scorpion", degree_in_sign=28.5, house=4, speed=13.0)
    slow = PointPosition(name="Saturne", sign="Sagittaire", degree_in_sign=0.5, house=5, speed=0.03)
    assert out_of_sign_conjunction(fast, slow) is True


def test_out_of_sign_conjunction_not_triggered_when_separating():
    # Même écart de 2°, mais la plus rapide s'éloigne au lieu d'appliquer.
    fast = PointPosition(name="Lune", sign="Sagittaire", degree_in_sign=0.5, house=5, speed=13.0)
    slow = PointPosition(name="Saturne", sign="Scorpion", degree_in_sign=28.5, house=4, speed=0.03)
    assert out_of_sign_conjunction(fast, slow) is False


def test_out_of_sign_conjunction_ignores_points_without_speed():
    asc = PointPosition(name="Ascendant", sign="Scorpion", degree_in_sign=28.5, house=1, speed=None)
    slow = PointPosition(name="Saturne", sign="Sagittaire", degree_in_sign=0.5, house=2, speed=0.03)
    assert out_of_sign_conjunction(asc, slow) is False


def test_compute_cluster_aspects_between_two_clusters():
    points = [
        PointPosition(name="Soleil", sign="Bélier", degree_in_sign=10, house=1, speed=1.0),
        PointPosition(name="Lune", sign="Cancer", degree_in_sign=10, house=4, speed=13.0),
    ]
    clusters = build_clusters(points)
    aspects = compute_cluster_aspects(clusters, points)
    assert len(aspects) == 1
    assert aspects[0].sign_a == "Bélier"
    assert aspects[0].sign_b == "Cancer"
    assert aspects[0].aspect == "Carré"
    assert aspects[0].boundary_exception is False
