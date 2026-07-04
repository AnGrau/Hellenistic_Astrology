from datetime import datetime, timezone

import matplotlib.pyplot as plt
import pytest

from hellenistic_astrology.core.aspects import ClusterAspect, SignCluster
from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.observation import Observation, PointPosition
from hellenistic_astrology.core.zodiacal_releasing import ReleasingChapter, ReleasingPeriod
from hellenistic_astrology.docgen import chart_image

from .regression_helpers import birth_data_from_fixture, load_fixture

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Pas de comparaison pixel par pixel (fragile, sans valeur réelle — voir le
# plan du jalon 33) : on vérifie seulement que chaque fonction s'exécute
# sans exception et produit un PNG non vide.


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_render_chart_wheel_on_reference_charts(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    png = chart_image.render_chart_wheel(observation)

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


def _wheel_label_and_marker_boxes(fig):
    """Bounding box (pixels) de chaque étiquette de texte et de chaque
    marqueur de point (`ax.plot(..., "o", gid="point:<nom>")`), avec le
    `gid` associé quand il existe — un marqueur et sa propre étiquette
    partagent le même `gid` (voir `render_chart_wheel`) et sont donc
    attendus proches l'un de l'autre, pas un vrai chevauchement."""
    ax = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    boxes = [(text.get_gid(), text.get_window_extent(renderer=renderer)) for text in ax.texts]
    boxes += [
        (line.get_gid(), line.get_window_extent(renderer=renderer))
        for line in ax.lines
        if line.get_gid() and line.get_gid().startswith("point:")
    ]
    return boxes


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_render_chart_wheel_labels_do_not_overlap(fixture_name):
    # Détection de chevauchement par bounding box (matplotlib), pas une
    # comparaison pixel par pixel : vérifie que les numéros de maison, les
    # glyphes de signe/point (marqueur ET étiquette), et les étiquettes
    # d'angle (AC/DC/MC/IC) ne se recouvrent jamais entre eux — sauf le
    # marqueur d'un point et sa propre étiquette, attendus proches par
    # construction (même `gid`) — sur la figure réellement dessinée par
    # `_build_chart_wheel_figure` (pas une réimplémentation séparée).
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    fig = chart_image._build_chart_wheel_figure(observation)
    fig.canvas.draw()
    boxes = _wheel_label_and_marker_boxes(fig)

    overlaps = [
        (i, j)
        for i in range(len(boxes))
        for j in range(i + 1, len(boxes))
        if boxes[i][1].overlaps(boxes[j][1]) and not (boxes[i][0] and boxes[i][0] == boxes[j][0])
    ]
    plt.close(fig)

    assert overlaps == []


@pytest.mark.parametrize("member_count", range(1, 7))
def test_cluster_point_radii_stays_above_aspect_hub(member_count):
    # Un amas resserré (jalon 36 : la Part de Fortune d'Anthony, 4e membre
    # du même signe, apparaissait visuellement à l'intérieur du diagramme
    # d'aspects) ne doit jamais placer un membre sous l'anneau d'aspect,
    # quel que soit le nombre de membres.
    radii, _ = chart_image._cluster_point_radii(member_count)

    assert len(radii) == member_count
    assert radii[0] == chart_image._POINT_BASE_RADIUS
    assert all(r > chart_image._ASPECT_HUB_RADIUS for r in radii)
    assert radii == sorted(radii, reverse=True)


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_render_elemental_modal_chart_on_reference_charts(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    png = chart_image.render_elemental_modal_chart(observation)

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_render_zodiacal_releasing_timeline_on_reference_charts(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    png = chart_image.render_zodiacal_releasing_timeline(
        observation.zodiacal_releasing_fortune,
        observation.zodiacal_releasing_spirit,
        observation.part_of_fortune.sign,
    )

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


def _minimal_observation() -> Observation:
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    soleil = PointPosition(name="Soleil", sign="Lion", degree_in_sign=10, house=5)
    return Observation(
        name="Test",
        sect="diurne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=[soleil],
        all_points=[ascendant, midheaven, soleil],
    )


def test_render_chart_wheel_minimal_observation_no_clusters_no_aspects():
    # Amas et aspects de cluster vides (valeurs par défaut d'Observation) :
    # vérifie que la roue reste dessinable sans aucun point ni ligne
    # d'aspect au-delà de l'Ascendant/Milieu du Ciel.
    observation = _minimal_observation()

    png = chart_image.render_chart_wheel(observation)

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


def test_render_chart_wheel_with_cluster_and_aspect():
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    soleil = PointPosition(name="Soleil", sign="Lion", degree_in_sign=10, house=5)
    lune = PointPosition(name="Lune", sign="Lion", degree_in_sign=15, house=5)
    mars = PointPosition(name="Mars", sign="Sagittaire", degree_in_sign=5, house=9)
    observation = Observation(
        name="Test",
        sect="diurne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=[soleil, lune, mars],
        all_points=[ascendant, midheaven, soleil, lune, mars],
        clusters=[
            SignCluster(sign="Lion", house=5, members=("Soleil", "Lune")),
            SignCluster(sign="Sagittaire", house=9, members=("Mars",)),
        ],
        cluster_aspects=[
            ClusterAspect(sign_a="Lion", sign_b="Sagittaire", aspect="Trigone"),
        ],
    )

    png = chart_image.render_chart_wheel(observation)

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


def test_render_elemental_modal_chart_minimal_observation():
    observation = _minimal_observation()

    png = chart_image.render_elemental_modal_chart(observation)

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0


def test_render_zodiacal_releasing_timeline_synthetic():
    l1_a = ReleasingPeriod(
        level=1, sign="Scorpion", ruler="Mars",
        start=datetime(2000, 1, 1, tzinfo=timezone.utc), end=datetime(2015, 1, 1, tzinfo=timezone.utc),
    )
    l1_b = ReleasingPeriod(
        level=1, sign="Sagittaire", ruler="Jupiter",
        start=datetime(2015, 1, 1, tzinfo=timezone.utc), end=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    chapters = [ReleasingChapter(l1=l1_a, sub_periods=[]), ReleasingChapter(l1=l1_b, sub_periods=[])]

    png = chart_image.render_zodiacal_releasing_timeline(chapters, chapters, "Scorpion")

    assert png.startswith(PNG_MAGIC)
    assert len(png) > 0
