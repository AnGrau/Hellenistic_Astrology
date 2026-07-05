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

HARD_ASPECT_COLOR = "#E74C3C"  # carré, opposition — éclairci pour rester lisible sur fond sombre
SOFT_ASPECT_COLOR = "#5DADE2"  # trigone, sextile — idem
_ASPECT_COLORS = {
    "Carré": HARD_ASPECT_COLOR,
    "Opposition": HARD_ASPECT_COLOR,
    "Trigone": SOFT_ASPECT_COLOR,
    "Sextile": SOFT_ASPECT_COLOR,
}

# Palette de la roue seule (jalon 37) : fond quasi noir plutôt que blanc,
# pour la lisibilité des nombreux petits glyphes/étiquettes qui s'y
# entassent — limité à `render_chart_wheel` : le graphique élément/modalité
# et la frise de libération zodiacale restent sur fond clair (décision
# explicite avec l'utilisateur, pas de repeinte des trois visuels).
# `ELEMENT_COLORS` reste inchangé (partagé avec ces deux autres visuels) :
# les teintes pastel gardent un bon contraste sur fond sombre sans qu'il
# faille les assombrir.
WHEEL_BACKGROUND_COLOR = "#0d0d1a"
WHEEL_HOUSE_NUMBER_COLOR = "#a9acc9"
WHEEL_ASPECT_HUB_COLOR = "#6d7096"
WHEEL_ANGLE_COLOR = "#d4ac0d"
WHEEL_POINT_MARKER_COLOR = "#f4f1ea"
WHEEL_POINT_LABEL_COLOR = "#f4f1ea"
WHEEL_POINT_BOX_FACECOLOR = "#1c1c2e"
WHEEL_POINT_BOX_EDGECOLOR = "#565979"
WHEEL_LEADER_LINE_COLOR = "#565979"
RETROGRADE_MARK = "℞"

_SIGN_RING_INNER = 0.78
_HOUSE_NUMBER_RADIUS = 0.745
_ASPECT_HUB_RADIUS = 0.25
# Jalon 43 : l'ensemble de cette section (rayons, pas, décalage) a été
# recalculé comme un système, pas constante par constante — augmenter un
# seul décalage sans revoir le pas radial déplace juste le chevauchement
# ailleurs (vécu en pratique : un premier essai à décalage=0.10/pas=0.14
# faisait recouvrir les numéros de maison par les étiquettes de palier 0,
# et les étiquettes de palier N+1 par les marqueurs du palier N). Les
# contraintes tenues simultanément, toutes mesurées directement (pas
# devinées) sur la boîte réellement rendue la plus large (glyphe
# rétrograde, ex. "♄℞" — plus large qu'un glyphe simple ou qu'un label de
# Lot) via `patch.get_window_extent` :
#   1. décalage marqueur -> étiquette > demi-diagonale de la boîte (sinon
#      une étiquette recouvre son PROPRE marqueur, jalon 43 : Part d'Éros
#      chez Anthony) — demi-diagonale mesurée ≈0,076 (police normale),
#      ≈0,051 (police resserrée).
#   2. pas radial > décalage + demi-diagonale (sinon l'étiquette du palier
#      N+1 recouvre le marqueur du palier N, plus proche du centre).
#   3. rayon de base + décalage + demi-diagonale < rayon des numéros de
#      maison, avec une marge (sinon l'étiquette du palier 0 recouvre les
#      numéros de maison, juste au-dessus).
_POINT_BASE_RADIUS = 0.55
# Rayon le plus bas qu'un amas peut atteindre en s'étageant (jalon 36) :
# garde une marge sûre au-dessus de l'anneau d'aspect ci-dessus, quel que
# soit le nombre de membres.
_POINT_INNER_FLOOR = 0.28
_POINT_RADIUS_STEP = 0.18
_POINT_LABEL_OFFSET = 0.09
_POINT_LABEL_OFFSET_CROWDED = 0.06
_POINT_FONTSIZE_GLYPH = 12
_POINT_FONTSIZE_LOT = 8
_POINT_FONTSIZE_GLYPH_CROWDED = 8
_POINT_FONTSIZE_LOT_CROWDED = 6
# Deux points à moins de cet écart angulaire réel se disputeraient le même
# rayon (jalon 40). Calibré au jalon 42 sur une mesure directe (pas une
# estimation) de la largeur réellement rendue de l'étiquette la plus large
# ("Fort.", boîte arrondie comprise) via `patch.get_window_extent` — jalon
# 40 s'était calibré sur la largeur du seul *texte* (~0.05 en unités de
# rayon), sans compter le padding de la boîte ajoutée au jalon 37, ce que
# `Text.get_window_extent` ne mesure jamais (angle mort corrigé dans
# `tests/test_chart_image.py::_text_window_extent`). Mesuré : ~10,75°
# d'empreinte angulaire pour "Fort." à `_POINT_BASE_RADIUS` — deux
# étiquettes de cette largeur au même palier se touchent donc déjà à ce
# seuil-là ; 13° laisse une marge de sécurité, revalidé empiriquement par
# la même détection de chevauchement par bounding box que les jalons
# 35/36/40 (voir tests/test_chart_image.py).
_ANGULAR_COLLISION_DEGREES = 13.0


def _angular_distance_degrees(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _assign_point_tiers(
    entries: list[tuple[str, float]], reserved_at_base_tier: list[float] = ()
) -> dict[str, int]:
    """Attribue un palier entier (0 = rayon de base, 1 = un cran plus interne,
    etc.) à chaque point d'affichage, un par un dans l'ordre des angles, en
    ne considérant que la proximité angulaire réelle
    (`_ANGULAR_COLLISION_DEGREES`) — pas l'appartenance à un même amas de
    signe (jalon 36), qui ne garantissait ni qu'un amas soit visuellement
    resserré (deux membres peuvent être à près de 30° l'un de l'autre dans
    le même signe) ni que deux amas de signes *voisins* soient assez
    éloignés l'un de l'autre : deux amas à un seul membre chacun, dans des
    signes adjacents mais à quelques degrés réels de la frontière commune,
    tombaient tous les deux sur le rayon de base et se chevauchaient malgré
    l'étagement par amas (retour utilisateur direct sur un thème réel,
    jalon 40).

    `entries` : liste de (nom, thêta en degrés). Premier palier disponible
    qui n'entre pas en collision avec un point déjà placé à moins de
    `_ANGULAR_COLLISION_DEGREES` — glouton, dans l'ordre des angles
    croissants, donc pas nécessairement optimal (un point peut recevoir un
    palier plus profond que strictement nécessaire) mais toujours sûr, dans
    le même esprit que l'étagement systématique déjà en place depuis le
    jalon 36.

    `reserved_at_base_tier` : thêtas (degrés) considérés comme occupant déjà
    le palier 0 avant même de traiter `entries` — utilisé pour les quatre
    angles AC/DC/MC/IC (jalon 42), dont l'étiquette est toujours au même
    rayon fixe, proche de celui du palier 0. Sans cette réservation, un
    point dont la longitude réelle tombe à quelques degrés d'un angle
    recevait quand même le palier 0 (les angles ne participaient à aucune
    détection de collision), et son étiquette chevauchait alors celle de
    l'angle — retour utilisateur direct sur un thème réel, seul le rayon
    fixe de l'angle étant assez proche du palier 0 pour poser problème (les
    paliers plus profonds sont déjà nettement plus bas)."""
    ordered = sorted(entries, key=lambda entry: entry[1] % 360.0)
    tiers: dict[str, int] = {}
    placed: list[tuple[float, int]] = [(theta, 0) for theta in reserved_at_base_tier]
    for name, theta in ordered:
        used_nearby = {
            tier
            for other_theta, tier in placed
            if _angular_distance_degrees(theta, other_theta) < _ANGULAR_COLLISION_DEGREES
        }
        tier = 0
        while tier in used_nearby:
            tier += 1
        tiers[name] = tier
        placed.append((theta, tier))
    return tiers


def _tier_radii(tier_count: int) -> tuple[list[float], bool]:
    """Rayons radiaux pour `tier_count` paliers (du plus externe, palier 0,
    au plus interne), plus un indicateur "crowded" (police et décalage
    d'étiquette réduits, voir `render_chart_wheel`) — même logique de
    compression que l'ancien `_cluster_point_radii` (jalon 36), désormais
    appliquée au nombre de paliers réellement utilisés sur l'ensemble de la
    roue (`_assign_point_tiers`) plutôt qu'au nombre de membres d'un seul
    amas de signe.

    Le pas `_POINT_RADIUS_STEP` s'applique tel quel tant que l'ensemble
    tient dans la bande [`_POINT_BASE_RADIUS`, `_POINT_INNER_FLOOR`] ;
    au-delà, le pas se resserre pour ne jamais descendre sous
    `_POINT_INNER_FLOOR`, quel que soit le nombre de paliers."""
    if tier_count <= 1:
        return [_POINT_BASE_RADIUS], False

    natural_span = _POINT_RADIUS_STEP * (tier_count - 1)
    if _POINT_BASE_RADIUS - natural_span >= _POINT_INNER_FLOOR:
        step = _POINT_RADIUS_STEP
        crowded = False
    else:
        step = (_POINT_BASE_RADIUS - _POINT_INNER_FLOOR) / (tier_count - 1)
        crowded = True
    return [_POINT_BASE_RADIUS - idx * step for idx in range(tier_count)], crowded


def _figure_to_png_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def _wheel_theta_degrees(longitude_degrees: float, ascendant_longitude: float) -> float:
    """Angle en degrés (0-360) pour une longitude écliptique donnée, dans le
    repère ancré sur l'Ascendant décrit par `_wheel_theta` — séparé de la
    conversion en radians pour que `_assign_point_tiers` (comparaisons
    angulaires en degrés) n'ait pas à repasser par un aller-retour
    radians -> degrés."""
    return (longitude_degrees - ascendant_longitude + 180) % 360


def _wheel_theta(longitude_degrees: float, ascendant_longitude: float) -> float:
    """Angle matplotlib (radians) pour une longitude écliptique donnée,
    dans un repère ancré sur l'Ascendant plutôt que sur le zodiaque fixe :
    convention universelle des roues de thème (Astro.com, Astro-Seek,
    Solar Fire...) — Ascendant toujours à gauche (9h, horizontal),
    Descendant à droite (3h), maisons dans l'ordre zodiacal en tournant
    dans le sens anti-horaire. Avec `theta_zero_location("E")` et
    `theta_direction(1)` (sens trigonométrique standard), un décalage de
    +180° place la longitude de l'Ascendant lui-même à l'Ouest (gauche)."""
    return np.radians(_wheel_theta_degrees(longitude_degrees, ascendant_longitude))


def render_chart_wheel(observation: Observation) -> bytes:
    """Roue du thème : voir `_build_chart_wheel_figure` pour le détail du
    dessin. Cette fonction ne fait que le convertir en PNG."""
    return _figure_to_png_bytes(_build_chart_wheel_figure(observation))


def _build_chart_wheel_figure(observation: Observation):
    """Construit la figure matplotlib de la roue du thème (sans la
    convertir en PNG ni fermer la figure) : 12 secteurs de signe (teinte
    par élément, réutilise `dignities.SIGN_TRIPLICITY`), glyphes de signe
    et de point placés par longitude réelle (`houses.longitude_of`),
    numéros de maison (whole sign, réutilise `houses.whole_sign_house`),
    les quatre angles (Ascendant/Descendant/Milieu du Ciel/Fond du Ciel)
    marqués par une ligne radiale distincte, lignes d'aspect entre amas
    (`observation.cluster_aspects`, aversions exclues) tracées à l'angle
    médian de chaque signe — fidèle à la méthodologie du projet (aspects
    par signe entre amas, pas des aspects degré-précis entre planètes
    individuelles). Planètes rétrogrades marquées du symbole ℞ à côté de
    leur glyphe (jalon 37) ; chaque point est en outre relié à l'anneau des
    signes par un fil de rappel discret, purement décoratif (le rayon
    étagé du jalon 36 ne change jamais l'angle). Fond sombre (jalon 37,
    voir `WHEEL_BACKGROUND_COLOR`), limité à cette roue : le graphique
    élément/modalité et la frise de libération zodiacale restent sur fond
    clair, décision explicite avec l'utilisateur.

    Le repère est ancré sur l'Ascendant (`_wheel_theta`), pas sur le
    zodiaque fixe : Ascendant/Descendant toujours horizontaux,
    Milieu du Ciel/Fond du Ciel à leur position réelle (qui dépend de la
    latitude, comme en whole-sign — pas nécessairement en haut/en bas).

    Figure séparée de `render_chart_wheel` (qui ne fait que la convertir en
    PNG) pour que les tests puissent inspecter les bounding boxes de texte
    (`tests/test_chart_image.py`, détection de chevauchement) sans dupliquer
    la logique de dessin."""
    fig = plt.figure(figsize=(7, 7))
    fig.patch.set_facecolor(WHEEL_BACKGROUND_COLOR)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_facecolor(WHEEL_BACKGROUND_COLOR)
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
        ax.text(theta_center, _HOUSE_NUMBER_RADIUS, str(house_num), ha="center", va="center", fontsize=9, color=WHEEL_HOUSE_NUMBER_COLOR)

    # Cercles de repère. Les deux limites de la couronne des signes (r=1.0
    # et r=_SIGN_RING_INNER) restent noires : elles bordent la couronne
    # pastel des deux côtés possibles (fond sombre à l'intérieur, coins du
    # subplot à l'extérieur) et le noir contraste correctement contre le
    # pastel dans les deux cas — seul l'anneau d'aspect, posé sur le disque
    # sombre, a besoin d'une couleur claire pour rester visible.
    theta_full = np.linspace(0, 2 * np.pi, 200)
    ax.plot(theta_full, [1.0] * 200, color="black", linewidth=1.2)
    ax.plot(theta_full, [_SIGN_RING_INNER] * 200, color="black", linewidth=0.8)
    ax.plot(theta_full, [_ASPECT_HUB_RADIUS] * 200, color=WHEEL_ASPECT_HUB_COLOR, linewidth=0.5, alpha=0.6)
    for i in range(12):
        theta = _wheel_theta(i * 30, ascendant_longitude)
        ax.plot([theta, theta], [_SIGN_RING_INNER, 1.0], color="black", linewidth=0.6)

    # Les quatre angles (Ascendant/Descendant/Milieu du Ciel/Fond du Ciel) :
    # calculés ici, avant les points, pour que leurs thêtas puissent réserver
    # le palier 0 (jalon 42) avant l'étagement des points — mais dessinés
    # plus bas, dans leur emplacement d'origine (l'ordre d'ajout ne change
    # pas l'empilement visuel, contrôlé par `zorder`).
    midheaven_longitude = longitude_of(observation.midheaven.sign, observation.midheaven.degree_in_sign)
    angles = [
        (ascendant_longitude, "AC"),
        ((ascendant_longitude + 180) % 360, "DC"),
        (midheaven_longitude, "MC"),
        ((midheaven_longitude + 180) % 360, "IC"),
    ]
    angle_theta_degrees = [_wheel_theta_degrees(longitude, ascendant_longitude) for longitude, _ in angles]

    # Points : rayon attribué par proximité angulaire réelle sur l'ensemble
    # de la roue (`_assign_point_tiers`, jalon 40), pas par appartenance à un
    # même amas de signe (jalon 36) — deux amas de signes voisins peuvent
    # être à quelques degrés réels l'un de l'autre et se disputer le même
    # rayon tout autant que deux membres d'un même amas. Les quatre angles
    # réservent aussi le palier 0 (jalon 42) : leur étiquette est à un rayon
    # fixe assez proche de celui du palier 0 pour s'y chevaucher sinon.
    # Chaque marqueur et son étiquette partagent un `gid` (`point:<nom>`) :
    # uniquement pour que les tests de non-chevauchement (jalon 36) puissent
    # distinguer un marqueur et sa propre étiquette (attendus proches l'un
    # de l'autre) d'un chevauchement avec un point différent (un vrai défaut
    # visuel).
    points_by_name = {p.name: p for p in observation.all_points}
    excluded_from_dots = {"Ascendant", "Milieu du Ciel"}
    display_names = [
        name for cluster in observation.clusters for name in cluster.members if name not in excluded_from_dots
    ]
    theta_degrees_by_name = {
        name: _wheel_theta_degrees(
            longitude_of(points_by_name[name].sign, points_by_name[name].degree_in_sign), ascendant_longitude
        )
        for name in display_names
    }
    tiers = _assign_point_tiers(list(theta_degrees_by_name.items()), reserved_at_base_tier=angle_theta_degrees)
    tier_count = max(tiers.values(), default=-1) + 1
    radii_by_tier, crowded = _tier_radii(tier_count)
    label_offset = _POINT_LABEL_OFFSET_CROWDED if crowded else _POINT_LABEL_OFFSET

    for name in display_names:
        point = points_by_name[name]
        theta = np.radians(theta_degrees_by_name[name])
        radius = radii_by_tier[tiers[name]]
        label = POINT_GLYPHS.get(name) or POINT_LABELS.get(name, name[:4])
        if point.retrograde:
            label += RETROGRADE_MARK
        is_glyph = name in POINT_GLYPHS
        if crowded:
            fontsize = _POINT_FONTSIZE_GLYPH_CROWDED if is_glyph else _POINT_FONTSIZE_LOT_CROWDED
        else:
            fontsize = _POINT_FONTSIZE_GLYPH if is_glyph else _POINT_FONTSIZE_LOT
        # Fil de rappel entre le marqueur et l'anneau des signes : purement
        # décoratif (le marqueur est déjà à la longitude réelle du point,
        # l'étagement ne modifie que le rayon, jamais l'angle). Sans `gid`
        # "point:*" volontairement : reste hors du test de non-chevauchement
        # (jalons 35/36), qui ne porte que sur les étiquettes et marqueurs
        # eux-mêmes, pas sur ce fil décoratif.
        ax.plot(
            [theta, theta], [radius, _SIGN_RING_INNER - 0.02],
            color=WHEEL_LEADER_LINE_COLOR, linewidth=0.5, alpha=0.5, zorder=1,
        )
        ax.plot(theta, radius, "o", color=WHEEL_POINT_MARKER_COLOR, markersize=4, gid=f"point:{name}", zorder=10)
        ax.text(
            theta, radius + label_offset, label, ha="center", va="center",
            fontsize=fontsize, color=WHEEL_POINT_LABEL_COLOR, fontweight="bold",
            gid=f"point:{name}", zorder=11,
            bbox=dict(
                boxstyle="round,pad=0.15", facecolor=WHEEL_POINT_BOX_FACECOLOR,
                edgecolor=WHEEL_POINT_BOX_EDGECOLOR, linewidth=0.8, alpha=0.92,
            ),
        )

    # Les quatre angles : Ascendant/Descendant et Milieu du Ciel/Fond du
    # Ciel sont chacun deux points diamétralement opposés (+180° de
    # longitude écliptique) — géométrie pure, pas un nouveau calcul
    # astrologique indépendant. Ligne radiale distincte plutôt qu'un
    # glyphe de planète (convention usuelle des roues de thème). `angles`
    # déjà calculé plus haut (réservation du palier 0, jalon 42).
    for longitude, label in angles:
        theta = _wheel_theta(longitude, ascendant_longitude)
        ax.plot([theta, theta], [0, _SIGN_RING_INNER], color=WHEEL_ANGLE_COLOR, linewidth=1.4, zorder=3)
        # Fond opaque derrière l'étiquette (jalon 40) : sans lui, la ligne —
        # de la même couleur, tracée jusqu'au même rayon que le texte — se
        # voyait par transparence entre les lettres ("AC"/"DC"/"MC"/"IC"
        # barrés, retour utilisateur direct sur un thème réel).
        ax.text(
            theta, _SIGN_RING_INNER - 0.05, label, ha="center", va="center", fontsize=10, fontweight="bold",
            color=WHEEL_ANGLE_COLOR, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", facecolor=WHEEL_BACKGROUND_COLOR, edgecolor="none"),
        )

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

    return fig


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
