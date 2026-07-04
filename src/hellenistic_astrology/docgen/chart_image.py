"""Rendu d'images (roue du thème, répartition élément/modalité, frise de
libération zodiacale) à partir d'un `Observation` déjà calculé — même
frontière que le reste de `docgen` (voir `docgen/CLAUDE.md`) : aucune
logique astrologique ici, uniquement du rendu de faits déjà calculés et
testés.

Dessiné à la main avec `matplotlib` plutôt qu'avec une bibliothèque de
thèmes existante (ex. `kerykeion`) : ces bibliothèques calculent les
positions avec leur propre moteur Swiss Ephemeris, indépendant de `core/`
— les utiliser introduirait un second moteur de calcul non vérifié à côté
de celui déjà testé de ce projet, avec un risque de divergence entre
l'image et les tableaux du même document (jalon 33).
"""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from ..core.dignities import SIGN_TRIPLICITY
from ..core.houses import SIGNS, index_of_sign, longitude_of, whole_sign_house
from ..core.observation import Observation
from ..core.zodiacal_releasing import ReleasingChapter, is_peak_period

ELEMENT_COLORS = {
    "Feu": "#F4B183",
    "Terre": "#A9D18E",
    "Air": "#FFE699",
    "Eau": "#9DC3E6",
}

SIGN_GLYPHS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌", "Vierge": "♍", "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓",
}

# Glyphes Unicode couverts nativement par la police par défaut de
# matplotlib dans cet environnement (vérifié directement avant ce jalon,
# pas une supposition). Les 3 Lots n'ont pas de glyphe standard reconnu :
# étiquette texte courte à la place, plutôt que d'inventer une convention.
POINT_GLYPHS = {
    "Soleil": "☉", "Lune": "☽", "Mercure": "☿", "Vénus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturne": "♄",
    "Nœud Nord": "☊", "Nœud Sud": "☋",
}
POINT_LABELS = {
    "Part de Fortune": "Fort.",
    "Part de l'Esprit": "Esp.",
    "Part d'Éros": "Éros",
}

HARD_ASPECT_COLOR = "#C0392B"  # carré, opposition
SOFT_ASPECT_COLOR = "#2471A3"  # trigone, sextile
_ASPECT_COLORS = {
    "Carré": HARD_ASPECT_COLOR,
    "Opposition": HARD_ASPECT_COLOR,
    "Trigone": SOFT_ASPECT_COLOR,
    "Sextile": SOFT_ASPECT_COLOR,
}

_SIGN_RING_INNER = 0.78
_HOUSE_NUMBER_RADIUS = 0.70
_ASPECT_HUB_RADIUS = 0.35
_POINT_BASE_RADIUS = 0.62
_POINT_RADIUS_STEP = 0.09


def _figure_to_png_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def _wheel_theta(longitude_degrees: float, ascendant_longitude: float) -> float:
    """Angle matplotlib (radians) pour une longitude écliptique donnée,
    dans un repère ancré sur l'Ascendant plutôt que sur le zodiaque fixe :
    convention universelle des roues de thème (Astro.com, Astro-Seek,
    Solar Fire...) — Ascendant toujours à gauche (9h, horizontal),
    Descendant à droite (3h), maisons dans l'ordre zodiacal en tournant
    dans le sens anti-horaire. Avec `theta_zero_location("E")` et
    `theta_direction(1)` (sens trigonométrique standard), un décalage de
    +180° place la longitude de l'Ascendant lui-même à l'Ouest (gauche)."""
    return np.radians((longitude_degrees - ascendant_longitude + 180) % 360)


def render_chart_wheel(observation: Observation) -> bytes:
    """Roue du thème : 12 secteurs de signe (teinte par élément, réutilise
    `dignities.SIGN_TRIPLICITY`), glyphes de signe et de point placés par
    longitude réelle (`houses.longitude_of`), numéros de maison (whole
    sign, réutilise `houses.whole_sign_house`), les quatre angles
    (Ascendant/Descendant/Milieu du Ciel/Fond du Ciel) marqués par une
    ligne radiale distincte, lignes d'aspect entre amas
    (`observation.cluster_aspects`, aversions exclues) tracées à l'angle
    médian de chaque signe — fidèle à la méthodologie du projet (aspects
    par signe entre amas, pas des aspects degré-précis entre planètes
    individuelles). Le repère est ancré sur l'Ascendant (`_wheel_theta`),
    pas sur le zodiaque fixe : Ascendant/Descendant toujours horizontaux,
    Milieu du Ciel/Fond du Ciel à leur position réelle (qui dépend de la
    latitude, comme en whole-sign — pas nécessairement en haut/en bas)."""
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_ylim(0, 1)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    ascendant_longitude = longitude_of(observation.ascendant.sign, observation.ascendant.degree_in_sign)

    # Secteurs de signe (teinte par élément) + glyphes + numéros de maison.
    for i, sign in enumerate(SIGNS):
        theta_center = _wheel_theta(i * 30 + 15, ascendant_longitude)
        color = ELEMENT_COLORS[SIGN_TRIPLICITY[sign]]
        ax.bar(
            theta_center, 1.0 - _SIGN_RING_INNER, width=np.radians(30), bottom=_SIGN_RING_INNER,
            color=color, edgecolor="black", linewidth=0.6,
        )
        ax.text(theta_center, (1.0 + _SIGN_RING_INNER) / 2, SIGN_GLYPHS[sign], ha="center", va="center", fontsize=14)
        house_num = whole_sign_house(i * 30, ascendant_longitude)
        ax.text(theta_center, _HOUSE_NUMBER_RADIUS, str(house_num), ha="center", va="center", fontsize=9, color="#555555")

    # Cercles de repère.
    theta_full = np.linspace(0, 2 * np.pi, 200)
    ax.plot(theta_full, [1.0] * 200, color="black", linewidth=1.2)
    ax.plot(theta_full, [_SIGN_RING_INNER] * 200, color="black", linewidth=0.8)
    ax.plot(theta_full, [_ASPECT_HUB_RADIUS] * 200, color="gray", linewidth=0.5, alpha=0.6)
    for i in range(12):
        theta = _wheel_theta(i * 30, ascendant_longitude)
        ax.plot([theta, theta], [_SIGN_RING_INNER, 1.0], color="black", linewidth=0.6)

    # Points, groupés par amas pour étager le rayon et éviter le
    # chevauchement des glyphes (les membres d'un même amas partagent un
    # signe donc des longitudes proches).
    points_by_name = {p.name: p for p in observation.all_points}
    excluded_from_dots = {"Ascendant", "Milieu du Ciel"}
    for cluster in observation.clusters:
        members = [m for m in cluster.members if m not in excluded_from_dots]
        for idx, name in enumerate(members):
            point = points_by_name[name]
            theta = _wheel_theta(longitude_of(point.sign, point.degree_in_sign), ascendant_longitude)
            radius = _POINT_BASE_RADIUS - idx * _POINT_RADIUS_STEP
            label = POINT_GLYPHS.get(name) or POINT_LABELS.get(name, name[:4])
            fontsize = 12 if name in POINT_GLYPHS else 8
            ax.plot(theta, radius, "o", color="#2E3B4E", markersize=4)
            ax.text(theta, radius + 0.06, label, ha="center", va="center", fontsize=fontsize, color="#2E3B4E")

    # Les quatre angles : Ascendant/Descendant et Milieu du Ciel/Fond du
    # Ciel sont chacun deux points diamétralement opposés (+180° de
    # longitude écliptique) — géométrie pure, pas un nouveau calcul
    # astrologique indépendant. Ligne radiale distincte plutôt qu'un
    # glyphe de planète (convention usuelle des roues de thème).
    midheaven_longitude = longitude_of(observation.midheaven.sign, observation.midheaven.degree_in_sign)
    angles = [
        (ascendant_longitude, "AC"),
        ((ascendant_longitude + 180) % 360, "DC"),
        (midheaven_longitude, "MC"),
        ((midheaven_longitude + 180) % 360, "IC"),
    ]
    for longitude, label in angles:
        theta = _wheel_theta(longitude, ascendant_longitude)
        ax.plot([theta, theta], [0, _SIGN_RING_INNER], color="#8B0000", linewidth=1.4)
        ax.text(theta, _SIGN_RING_INNER - 0.05, label, ha="center", va="center", fontsize=10, fontweight="bold", color="#8B0000")

    # Lignes d'aspect entre amas, à l'angle médian de chaque signe (pas la
    # longitude réelle des points : ce projet calcule des aspects par
    # signe entre amas, pas des aspects degré-précis entre planètes).
    for cluster_aspect in observation.cluster_aspects:
        color = _ASPECT_COLORS.get(cluster_aspect.aspect)
        if color is None:
            continue  # Aversion (ou cas hors-signe non représenté ici).
        theta_a = _wheel_theta(index_of_sign(cluster_aspect.sign_a) * 30 + 15, ascendant_longitude)
        theta_b = _wheel_theta(index_of_sign(cluster_aspect.sign_b) * 30 + 15, ascendant_longitude)
        ax.plot([theta_a, theta_b], [_ASPECT_HUB_RADIUS, _ASPECT_HUB_RADIUS], color=color, linewidth=1.0, alpha=0.75)

    return _figure_to_png_bytes(fig)


def render_elemental_modal_chart(observation: Observation) -> bytes:
    """Graphique à barres élément/modalité — réutilise la convention des 12
    points déjà établie (`docgen.builder._distribution_points`, jalon 19),
    aucun recalcul."""
    from .builder import _distribution_points  # import tardif : évite le cycle builder -> chart_image -> builder.

    points = _distribution_points(observation)
    element_order = ["Feu", "Terre", "Air", "Eau"]
    modality_order = ["Cardinal", "Fixe", "Mutable"]
    element_counts = [sum(1 for p in points if p.element == e) for e in element_order]
    modality_counts = [sum(1 for p in points if p.modality == m) for m in modality_order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3))
    ax1.bar(element_order, element_counts, color=[ELEMENT_COLORS[e] for e in element_order], edgecolor="black")
    ax1.set_title("Éléments", fontsize=11)
    ax1.set_ylabel("Facteurs")
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax2.bar(modality_order, modality_counts, color="#B7B7C6", edgecolor="black")
    ax2.set_title("Modalité", fontsize=11)
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    return _figure_to_png_bytes(fig)


def render_zodiacal_releasing_timeline(
    chapters_fortune: list[ReleasingChapter],
    chapters_spirit: list[ReleasingChapter],
    fortune_sign: str,
) -> bytes:
    """Frise horizontale des périodes majeures (L1) de libération
    zodiacale, Fortune et Esprit — couleur par élément du signe (cohérent
    avec la roue), périodes culminantes marquées par un contour plus épais
    (réutilise `is_peak_period`, déjà testée, jalon 17). Niveau L1
    seulement, pour la lisibilité sur l'horizon de 100 ans (jalon 18)."""
    fig, ax = plt.subplots(figsize=(9, 2.2))
    rows = [("Part de l'Esprit", chapters_spirit), ("Part de Fortune", chapters_fortune)]
    for row_index, (label, chapters) in enumerate(rows):
        for chapter in chapters:
            period = chapter.l1
            start_num = mdates.date2num(period.start)
            end_num = mdates.date2num(period.end)
            color = ELEMENT_COLORS[SIGN_TRIPLICITY[period.sign]]
            linewidth = 1.8 if is_peak_period(period, fortune_sign) else 0.6
            ax.barh(
                row_index, end_num - start_num, left=start_num, height=0.6,
                color=color, edgecolor="black", linewidth=linewidth,
            )
            ax.text((start_num + end_num) / 2, row_index, period.sign, ha="center", va="center", fontsize=7)
    ax.set_yticks([0, 1])
    ax.set_yticklabels([label for label, _ in rows])
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Année")
    fig.autofmt_xdate()
    fig.tight_layout()
    return _figure_to_png_bytes(fig)
