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


def _text_window_extent(text, renderer):
    """Bounding box réellement rendue d'un `Text` : celle de la boîte
    arrondie (`bbox=...`) si l'étiquette en a une, pas seulement celle des
    glyphes. `Text.get_window_extent` ne mesure QUE le texte lui-même —
    jamais le `FancyBboxPatch` ajouté par `bbox=` (jalon 37, glyphes de
    point et étiquettes d'angle) — donc deux étiquettes voisines pouvaient
    se chevaucher visuellement (le padding de la boîte les fait déborder)
    sans que ce test, avant cette correction, ne le détecte jamais (angle
    mort découvert par retour utilisateur direct après le jalon 40, qui
    n'avait donc été calibré que contre une mesure trop optimiste)."""
    patch = text.get_bbox_patch()
    if patch is not None:
        return patch.get_window_extent(renderer=renderer)
    return text.get_window_extent(renderer=renderer)


def _wheel_label_and_marker_boxes(fig):
    """Bounding box (pixels) de chaque étiquette de texte (boîte arrondie
    incluse quand elle existe, voir `_text_window_extent`) et de chaque
    marqueur de point (`ax.plot(..., "o", gid="point:<nom>")`), avec le
    `gid` associé quand il existe — un marqueur et sa propre étiquette
    partagent le même `gid` (voir `render_chart_wheel`) et sont donc
    attendus proches l'un de l'autre, pas un vrai chevauchement."""
    ax = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    boxes = [(text.get_gid(), _text_window_extent(text, renderer)) for text in ax.texts]
    boxes += [
        (line.get_gid(), line.get_window_extent(renderer=renderer))
        for line in ax.lines
        if line.get_gid() and line.get_gid().startswith("point:")
    ]
    return boxes


def _wheel_overlaps(fig) -> list[tuple[int, int]]:
    """Paires d'index de `_wheel_label_and_marker_boxes(fig)` dont les
    bounding boxes se chevauchent, hors marqueur/étiquette d'un même point
    (même `gid`, chevauchement attendu par construction)."""
    boxes = _wheel_label_and_marker_boxes(fig)
    return [
        (i, j)
        for i in range(len(boxes))
        for j in range(i + 1, len(boxes))
        if boxes[i][1].overlaps(boxes[j][1]) and not (boxes[i][0] and boxes[i][0] == boxes[j][0])
    ]


def _markers_hidden_by_own_label(fig) -> list[str]:
    """Noms (gid) des points dont le marqueur tombe à l'intérieur de la
    boîte de sa PROPRE étiquette — un vrai défaut depuis que les étiquettes
    ont un fond opaque (jalon 37) : avant, marqueur et étiquette pouvaient
    se chevaucher sans problème (texte sans fond), d'où l'exclusion
    délibérée de cette paire (même `gid`) dans `_wheel_overlaps`. Ce
    contrôle séparé rattrape le cas où cette exclusion masquait un vrai
    problème (jalon 43 : Part d'Éros chez Anthony, marqueur entièrement
    recouvert par sa propre boîte d'étiquette, découvert par retour
    utilisateur direct)."""
    ax = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    label_boxes_by_gid = {
        text.get_gid(): text.get_bbox_patch().get_window_extent(renderer=renderer)
        for text in ax.texts
        if text.get_gid() and text.get_gid().startswith("point:") and text.get_bbox_patch() is not None
    }
    hidden = []
    for line in ax.lines:
        gid = line.get_gid()
        if not gid or gid not in label_boxes_by_gid:
            continue
        (theta, radius), = line.get_xydata()
        px, py = ax.transData.transform((theta, radius))
        if label_boxes_by_gid[gid].contains(px, py):
            hidden.append(gid)
    return hidden


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_render_chart_wheel_markers_not_hidden_by_own_label(fixture_name):
    fixture = load_fixture(fixture_name)
    observation = build_observation(birth_data_from_fixture(fixture))

    fig = chart_image._build_chart_wheel_figure(observation)
    fig.canvas.draw()
    hidden = _markers_hidden_by_own_label(fig)
    plt.close(fig)

    assert hidden == []


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
    overlaps = _wheel_overlaps(fig)
    plt.close(fig)

    assert overlaps == []


def test_render_chart_wheel_lone_points_in_adjacent_signs_do_not_overlap():
    # Retour utilisateur direct sur un thème réel (jalon 40) : deux amas à
    # un seul membre chacun, dans des signes adjacents mais à seulement 2°
    # réels de la frontière commune, se chevauchaient avant la correction —
    # l'étagement par amas de signe (jalon 36) ne protégeait que les
    # membres d'un même amas, pas deux amas voisins proches en angle.
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    soleil = PointPosition(name="Soleil", sign="Taureau", degree_in_sign=29, house=2)
    lune = PointPosition(name="Lune", sign="Gémeaux", degree_in_sign=1, house=3)
    observation = Observation(
        name="Test",
        sect="diurne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=[soleil, lune],
        all_points=[ascendant, midheaven, soleil, lune],
        clusters=[
            SignCluster(sign="Taureau", house=2, members=("Soleil",)),
            SignCluster(sign="Gémeaux", house=3, members=("Lune",)),
        ],
    )

    fig = chart_image._build_chart_wheel_figure(observation)
    fig.canvas.draw()
    overlaps = _wheel_overlaps(fig)
    plt.close(fig)

    assert overlaps == []


def test_render_chart_wheel_points_near_angles_do_not_overlap_angle_labels():
    # Retour utilisateur direct sur un thème réel (jalon 42) : découvert en
    # corrigeant la mesure de bounding box du test (`_text_window_extent`,
    # qui ne comptait pas le padding des boîtes avant cette correction, un
    # angle mort du jalon 37 jamais détecté jusqu'ici). Un point dont la
    # longitude réelle tombe à quelques degrés d'un angle (AC/DC/MC/IC)
    # chevauchait l'étiquette de cet angle : `_assign_point_tiers` et la
    # boucle de dessin des angles ne se connaissaient pas l'un l'autre. Un
    # point à 2° de chacun des quatre angles, pas seulement de celui (IC,
    # chez Anthony) découvert par hasard.
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    soleil = PointPosition(name="Soleil", sign="Bélier", degree_in_sign=2, house=1)  # près de AC
    lune = PointPosition(name="Lune", sign="Balance", degree_in_sign=2, house=7)  # près de DC
    mercure = PointPosition(name="Mercure", sign="Capricorne", degree_in_sign=2, house=10)  # près de MC
    venus = PointPosition(name="Vénus", sign="Cancer", degree_in_sign=2, house=4)  # près de IC
    observation = Observation(
        name="Test",
        sect="diurne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=[soleil, lune, mercure, venus],
        all_points=[ascendant, midheaven, soleil, lune, mercure, venus],
        clusters=[
            SignCluster(sign="Bélier", house=1, members=("Soleil",)),
            SignCluster(sign="Balance", house=7, members=("Lune",)),
            SignCluster(sign="Capricorne", house=10, members=("Mercure",)),
            SignCluster(sign="Cancer", house=4, members=("Vénus",)),
        ],
    )

    fig = chart_image._build_chart_wheel_figure(observation)
    fig.canvas.draw()
    overlaps = _wheel_overlaps(fig)
    plt.close(fig)

    assert overlaps == []


@pytest.mark.parametrize("member_count", range(4, 9))
def test_render_chart_wheel_tightly_packed_cluster_does_not_overlap(member_count):
    # Jalon 42 : la correction de mesure (`_text_window_extent`) a révélé
    # que 6 points mutuellement proches (tous à moins de 4° de leur voisin,
    # dans un même signe) se chevauchaient sous l'ancien seuil angulaire
    # (9°, calibré sur une mesure de texte seul, jalon 40) malgré
    # l'étagement radial en mode "resserré" (jalon 36). Recalibré à 13°
    # (mesure directe de la largeur réellement rendue de "Fort.", boîte
    # comprise) : revalidé ici jusqu'à 8 membres (les 7 planètes classiques
    # + un nœud), au-delà de ce qu'aucun des deux thèmes de référence ne
    # présente (4 membres, le maximum observé, chez Anthony).
    ascendant = PointPosition(name="Ascendant", sign="Bélier", degree_in_sign=0, house=1)
    midheaven = PointPosition(name="Milieu du Ciel", sign="Capricorne", degree_in_sign=0, house=10)
    names = ["Soleil", "Lune", "Mercure", "Vénus", "Mars", "Jupiter", "Saturne", "Nœud Nord"][:member_count]
    degrees = [1, 5, 9, 13, 17, 21, 25, 29][:member_count]
    planets = [PointPosition(name=n, sign="Scorpion", degree_in_sign=d, house=8) for n, d in zip(names, degrees)]
    observation = Observation(
        name="Test",
        sect="diurne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=planets,
        all_points=[ascendant, midheaven, *planets],
        clusters=[SignCluster(sign="Scorpion", house=8, members=tuple(names))],
    )

    fig = chart_image._build_chart_wheel_figure(observation)
    fig.canvas.draw()
    overlaps = _wheel_overlaps(fig)
    plt.close(fig)

    assert overlaps == []


@pytest.mark.parametrize("tier_count", range(1, 7))
def test_tier_radii_stays_above_aspect_hub(tier_count):
    # Un ensemble resserré (jalon 36 : la Part de Fortune d'Anthony, 4e
    # membre du même signe, apparaissait visuellement à l'intérieur du
    # diagramme d'aspects) ne doit jamais placer un palier sous l'anneau
    # d'aspect, quel que soit le nombre de paliers réellement utilisés.
    radii, _ = chart_image._tier_radii(tier_count)

    assert len(radii) == tier_count
    assert radii[0] == chart_image._POINT_BASE_RADIUS
    assert all(r > chart_image._ASPECT_HUB_RADIUS for r in radii)
    assert radii == sorted(radii, reverse=True)


def test_assign_point_tiers_separates_angularly_close_points():
    tiers = chart_image._assign_point_tiers([("A", 10.0), ("B", 12.0)])
    assert tiers["A"] != tiers["B"]


def test_assign_point_tiers_reuses_base_tier_when_far_apart():
    tiers = chart_image._assign_point_tiers([("A", 10.0), ("B", 200.0)])
    assert tiers["A"] == 0
    assert tiers["B"] == 0


def test_assign_point_tiers_handles_wraparound_at_0_360():
    tiers = chart_image._assign_point_tiers([("A", 358.0), ("B", 2.0)])
    assert tiers["A"] != tiers["B"]


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
