import pytest

from hellenistic_astrology.core.aspects import ClusterAspect, SignCluster
from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.dignities import MutualReception
from hellenistic_astrology.docgen.builder import (
    POSITIONS_HEADER,
    RULERSHIPS_HEADER,
    build_observation_document,
    cluster_aspect_text,
    conjunction_text,
    direction_label,
    format_dms,
    mutual_reception_text,
)

from .regression_helpers import birth_data_from_fixture, load_fixture


@pytest.mark.parametrize(
    "decimal_degrees, expected",
    [
        (28.1833, "28°11'"),
        (0.2167, "0°13'"),
        (19.9833, "19°59'"),
        (27.9999, "28°00'"),  # ne doit jamais produire "27°60'"
    ],
)
def test_format_dms(decimal_degrees, expected):
    assert format_dms(decimal_degrees) == expected


def test_direction_label_gender_agreement():
    assert direction_label("Soleil", False) == "Direct"
    assert direction_label("Lune", False) == "Directe"
    assert direction_label("Vénus", True) == "Rétrograde"
    assert direction_label("Mars", True) == "Rétrograde"
    assert direction_label("Ascendant", None) == "—"


def test_conjunction_text_single_member_is_none():
    cluster = SignCluster(sign="Balance", house=3, members=("Mars",))
    assert conjunction_text(cluster) is None


def test_conjunction_text_mixed_gender_uses_masculine_plural():
    cluster = SignCluster(sign="Lion", house=1, members=("Ascendant", "Lune"))
    assert conjunction_text(cluster) == "l'Ascendant et Lune conjoints en Lion (maison 1)."


def test_conjunction_text_all_feminine_uses_feminine_plural():
    cluster = SignCluster(sign="Scorpion", house=4, members=("Lune", "Vénus"))
    assert conjunction_text(cluster) == "Lune et Vénus conjointes en Scorpion (maison 4)."


def test_conjunction_text_three_members_with_article():
    cluster = SignCluster(
        sign="Taureau", house=10, members=("Saturne", "Milieu du Ciel", "Part de l'Esprit")
    )
    assert conjunction_text(cluster) == (
        "Saturne, le Milieu du Ciel et la Part de l'Esprit conjoints en Taureau (maison 10)."
    )


def test_cluster_aspect_text_real_aspect():
    clusters_by_sign = {
        "Lion": SignCluster(sign="Lion", house=1, members=("Ascendant",)),
        "Scorpion": SignCluster(sign="Scorpion", house=4, members=("Soleil",)),
    }
    aspect = ClusterAspect(sign_a="Lion", sign_b="Scorpion", aspect="Carré")
    assert cluster_aspect_text(aspect, clusters_by_sign) == (
        "Lion (maison 1) en carré avec Scorpion (maison 4)."
    )


def test_cluster_aspect_text_boundary_exception():
    clusters_by_sign = {
        "Scorpion": SignCluster(sign="Scorpion", house=4, members=("Lune",)),
        "Sagittaire": SignCluster(sign="Sagittaire", house=5, members=("Saturne",)),
    }
    aspect = ClusterAspect(
        sign_a="Scorpion", sign_b="Sagittaire", aspect="Aversion", boundary_exception=True
    )
    assert cluster_aspect_text(aspect, clusters_by_sign) == (
        "Scorpion (maison 4) et Sagittaire (maison 5) : conjonction hors signe "
        "(règle des 3°, signes adjacents)."
    )


def test_mutual_reception_text():
    reception = MutualReception(planet_a="Vénus", planet_b="Mars")
    assert mutual_reception_text(reception) == (
        "Réception mutuelle par domicile entre Vénus et Mars."
    )


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_build_observation_document_structure(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    document = build_observation_document(observation)

    assert [p.text for p in document.paragraphs if p.style.name == "Heading 1"] == [
        "Phase 1 — Observation"
    ]
    assert len(document.tables) == 2

    positions_table, rulerships_table = document.tables

    header_row = [cell.text for cell in positions_table.rows[0].cells]
    assert header_row == POSITIONS_HEADER
    # Ascendant + 7 planètes classiques + Nœud Nord + Nœud Sud + MC + Fortune + Esprit + Éros.
    assert len(positions_table.rows) == 1 + 1 + 7 + 2 + 1 + 3

    ascendant_row = [cell.text for cell in positions_table.rows[1].cells]
    assert ascendant_row[0] == "Ascendant"
    assert ascendant_row[1] == fixture["ascendant"]["sign"]
    assert ascendant_row[3] == str(fixture["ascendant"]["house"])

    sun_row = next(
        [cell.text for cell in row.cells]
        for row in positions_table.rows
        if row.cells[0].text == "Soleil"
    )
    expected_sun = fixture["planets"]["Soleil"]
    assert sun_row[1] == expected_sun["sign"]
    assert sun_row[3] == str(expected_sun["house"])
    assert sun_row[4] == expected_sun["sect_role"]
    assert sun_row[6] == expected_sun["essential_dignity"]

    ruler_header = [cell.text for cell in rulerships_table.rows[0].cells]
    assert ruler_header == RULERSHIPS_HEADER
    assert len(rulerships_table.rows) == 1 + 7

    mercury_row = next(
        [cell.text for cell in row.cells]
        for row in rulerships_table.rows
        if row.cells[0].text == "Mercure"
    )
    expected_mercury = fixture["rulerships"]["Mercure"]
    assert mercury_row[1] == ", ".join(expected_mercury["domicile_signs"])
    assert mercury_row[2] == ", ".join(str(h) for h in expected_mercury["houses_governed"])

    heading2_texts = [p.text for p in document.paragraphs if p.style.name == "Heading 2"]
    assert heading2_texts[-1] == "Aspects par signe relevés"

    fixture_clusters = [
        SignCluster(sign=c["sign"], house=c["house"], members=tuple(c["members"]))
        for c in fixture["clusters"]
    ]
    clusters_by_sign = {c.sign: c for c in fixture_clusters}
    expected_bullets = [
        text for text in (conjunction_text(c) for c in fixture_clusters) if text is not None
    ]
    expected_bullets += [
        cluster_aspect_text(
            ClusterAspect(
                sign_a=a["sign_a"],
                sign_b=a["sign_b"],
                aspect=a["aspect"],
                boundary_exception=a["boundary_exception"],
            ),
            clusters_by_sign,
        )
        for a in fixture["cluster_aspects"]
    ]
    expected_bullets += [
        mutual_reception_text(MutualReception(planet_a=r["planet_a"], planet_b=r["planet_b"]))
        for r in fixture["mutual_receptions"]
    ]

    actual_bullets = [p.text for p in document.paragraphs if p.style.name == "List Bullet"]
    assert actual_bullets == expected_bullets
