from datetime import datetime

from docx import Document
import pytest

from hellenistic_astrology.core import dignities as dignities_module
from hellenistic_astrology.core.aspects import ClusterAspect, SignCluster
from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.dignities import MutualReception
from hellenistic_astrology.core.observation import Observation, PointPosition
from hellenistic_astrology.core.zodiacal_releasing import ReleasingChapter, ReleasingPeriod
from hellenistic_astrology.docgen.builder import (
    MINOR_DIGNITIES_HEADER,
    POSITIONS_HEADER,
    RULERSHIPS_HEADER,
    ZODIACAL_RELEASING_HEADER,
    add_minor_dignities_table,
    add_zodiacal_releasing_table,
    build_observation_document,
    cluster_aspect_text,
    conjunction_text,
    direction_label,
    format_dms,
    format_releasing_date,
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


def test_add_minor_dignities_table_uses_dash_for_missing_values():
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    planets = [
        PointPosition(
            name="Mars",
            sign="Bélier",
            degree_in_sign=3,
            house=1,
            triplicity_dignity="Maître de triplicité (jour)",
            bound_dignity=None,
            decan_dignity="Maître du décan",
        ),
        PointPosition(name="Vénus", sign="Bélier", degree_in_sign=3, house=1),
    ]
    observation = Observation(
        name="Test", sect="diurne", ascendant=ascendant, midheaven=midheaven, planets=planets
    )
    document = Document()

    table = add_minor_dignities_table(document, observation)

    mars_row = [cell.text for cell in table.rows[1].cells]
    assert mars_row == ["Mars", "Maître de triplicité (jour)", "—", "Maître du décan"]
    venus_row = [cell.text for cell in table.rows[2].cells]
    assert venus_row == ["Vénus", "—", "—", "—"]


def test_format_releasing_date():
    assert format_releasing_date(datetime(1970, 11, 20)) == "20/11/1970"


def test_add_zodiacal_releasing_table_rows_and_peak_marking():
    # Fortune synthétique en Scorpion : Lion (angulaire, groupe fixe) doit
    # être marqué culminant, Vierge (non angulaire à Scorpion) ne doit pas
    # l'être.
    fortune_sign = "Scorpion"
    l1 = ReleasingPeriod(
        level=1, sign="Lion", ruler="Soleil", start=datetime(2000, 1, 1), end=datetime(2019, 1, 1)
    )
    l2 = ReleasingPeriod(
        level=2, sign="Vierge", ruler="Mercure", start=datetime(2000, 1, 1), end=datetime(2001, 8, 1)
    )
    chapters = [ReleasingChapter(l1=l1, sub_periods=[l2])]
    document = Document()

    table = add_zodiacal_releasing_table(document, chapters, fortune_sign)

    header_row = [cell.text for cell in table.rows[0].cells]
    assert header_row == ZODIACAL_RELEASING_HEADER
    l1_row = [cell.text for cell in table.rows[1].cells]
    assert l1_row == ["L1", "Lion", "Soleil", "01/01/2000", "01/01/2019", "Oui"]
    l2_row = [cell.text for cell in table.rows[2].cells]
    assert l2_row == ["L2", "Vierge", "Mercure", "01/01/2000", "01/08/2001", "—"]


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_build_observation_document_structure(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    document = build_observation_document(observation)

    assert [p.text for p in document.paragraphs if p.style.name == "Heading 1"] == [
        "Phase 1 — Observation"
    ]
    assert len(document.tables) == 5

    (
        positions_table,
        rulerships_table,
        minor_dignities_table,
        zr_fortune_table,
        zr_spirit_table,
    ) = document.tables

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

    minor_header = [cell.text for cell in minor_dignities_table.rows[0].cells]
    assert minor_header == MINOR_DIGNITIES_HEADER
    assert len(minor_dignities_table.rows) == 1 + 7

    # Recalcule les valeurs attendues depuis les mêmes fonctions core.dignities,
    # appliquées à la position réellement calculée (pas la fixture, sujette à
    # une tolérance d'arrondi qui pourrait tomber près d'une frontière de
    # borne/décan) : ceci teste le branchement docgen, pas l'exactitude
    # astrologique déjà couverte par tests/test_dignities.py.
    for row in minor_dignities_table.rows[1:]:
        planet_name, triplicity_cell, bound_cell, decan_cell = (c.text for c in row.cells)
        actual_planet = observation.planet(planet_name)
        assert triplicity_cell == (
            dignities_module.triplicity_dignity(planet_name, actual_planet.sign) or "—"
        )
        assert bound_cell == (
            dignities_module.bound_dignity(
                planet_name, actual_planet.sign, actual_planet.degree_in_sign
            )
            or "—"
        )
        assert decan_cell == (
            dignities_module.decan_dignity(
                planet_name, actual_planet.sign, actual_planet.degree_in_sign
            )
            or "—"
        )

    heading2_texts = [p.text for p in document.paragraphs if p.style.name == "Heading 2"]
    assert heading2_texts[-2:] == [
        "Libération zodiacale — Part de Fortune",
        "Libération zodiacale — Part de l'Esprit",
    ]
    assert "Dignités mineures (triplicité, bornes, décans)" in heading2_texts
    assert "Aspects par signe relevés" in heading2_texts

    # Recoupe le rendu docgen contre le même calcul core.zodiacal_releasing,
    # sur la position réellement calculée (pas la fixture, qui ne documente
    # pas cette technique) : teste le branchement, pas l'exactitude
    # astrologique déjà couverte par tests/test_zodiacal_releasing.py.
    for table, chapters in [
        (zr_fortune_table, observation.zodiacal_releasing_fortune),
        (zr_spirit_table, observation.zodiacal_releasing_spirit),
    ]:
        assert [cell.text for cell in table.rows[0].cells] == ZODIACAL_RELEASING_HEADER
        expected_row_count = 1 + sum(1 + len(chapter.sub_periods) for chapter in chapters)
        assert len(table.rows) == expected_row_count
        first_l1_row = [cell.text for cell in table.rows[1].cells]
        assert first_l1_row[0] == "L1"
        assert first_l1_row[1] == chapters[0].l1.sign
        assert first_l1_row[3] == format_releasing_date(chapters[0].l1.start)

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
