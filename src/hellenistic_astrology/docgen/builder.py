from datetime import datetime

from docx import Document

from ..core.aspects import ClusterAspect, SignCluster
from ..core.dignities import MutualReception
from ..core.houses import house_quality
from ..core.observation import Observation, PointPosition
from ..core.zodiacal_releasing import ReleasingChapter, ReleasingPeriod, is_peak_period
from . import styles

FEMININE_PLANETS = {"Lune", "Vénus"}
FEMININE_POINTS = FEMININE_PLANETS | {"Part de Fortune", "Part de l'Esprit", "Part d'Éros"}

# Noms affichés avec article, pour les puces d'aspects (les planètes et les
# nœuds s'affichent sans article, comme dans les documents de référence).
DISPLAY_NAME_WITH_ARTICLE = {
    "Ascendant": "l'Ascendant",
    "Milieu du Ciel": "le Milieu du Ciel",
    "Part de Fortune": "la Part de Fortune",
    "Part de l'Esprit": "la Part de l'Esprit",
    "Part d'Éros": "la Part d'Éros",
}

ASPECT_LABEL = {
    "Sextile": "sextile",
    "Carré": "carré",
    "Trigone": "trigone",
    "Opposition": "opposition",
    "Aversion": "aversion",
}

POSITIONS_HEADER = ["Astre", "Signe", "Degré", "Maison", "Rôle de secte", "Direction", "Dignité essentielle"]
POSITIONS_COLUMN_WIDTHS_DXA = [1700, 1300, 1100, 900, 1900, 1300, 1600]

RULERSHIPS_HEADER = ["Planète", "Domiciles gouvernés", "Maisons régies depuis l'Ascendant"]
RULERSHIPS_COLUMN_WIDTHS_DXA = [2400, 3200, 3200]

MINOR_DIGNITIES_HEADER = ["Astre", "Triplicité", "Terme (bornes égyptiennes)", "Décan"]
MINOR_DIGNITIES_COLUMN_WIDTHS_DXA = [1700, 2900, 2900, 2300]

ZODIACAL_RELEASING_HEADER = ["Niveau", "Signe", "Maître", "Début", "Fin", "Culminante"]
ZODIACAL_RELEASING_COLUMN_WIDTHS_DXA = [900, 1700, 1700, 1600, 1600, 1400]


def format_dms(decimal_degrees: float) -> str:
    """Formate un degré décimal dans le signe en notation degrés/minutes.

    Arrondit et reporte la retenue sur le degré plutôt que de produire une
    notation invalide comme "27°60'" (60' = 1°).
    """
    degrees = int(decimal_degrees)
    minutes = round((decimal_degrees - degrees) * 60)
    if minutes == 60:
        minutes = 0
        degrees += 1
    return f"{degrees}°{minutes:02d}'"


def direction_label(name: str, retrograde: bool | None) -> str:
    if retrograde is None:
        return "—"
    if retrograde:
        return "Rétrograde"
    return "Directe" if name in FEMININE_PLANETS else "Direct"


def _positions_row(table, point: PointPosition) -> None:
    cells = table.add_row().cells
    cells[0].text = point.name
    cells[1].text = point.sign
    cells[2].text = format_dms(point.degree_in_sign)
    cells[3].text = str(point.house)
    cells[4].text = point.sect_role or "—"
    cells[5].text = direction_label(point.name, point.retrograde)
    cells[6].text = point.essential_dignity or "—"


def add_positions_table(document: Document, observation: Observation):
    table = document.add_table(rows=1, cols=len(POSITIONS_HEADER))
    for cell, text in zip(table.rows[0].cells, POSITIONS_HEADER):
        styles.set_header_cell(cell, text)
    styles.style_table(table, POSITIONS_COLUMN_WIDTHS_DXA)

    for point in observation.all_points:
        _positions_row(table, point)
    return table


def add_rulerships_table(document: Document, observation: Observation):
    table = document.add_table(rows=1, cols=len(RULERSHIPS_HEADER))
    for cell, text in zip(table.rows[0].cells, RULERSHIPS_HEADER):
        styles.set_header_cell(cell, text)
    styles.style_table(table, RULERSHIPS_COLUMN_WIDTHS_DXA)

    for rulership in observation.rulerships:
        cells = table.add_row().cells
        cells[0].text = rulership.planet
        cells[1].text = ", ".join(rulership.domicile_signs)
        cells[2].text = ", ".join(str(house) for house in rulership.houses_governed)
    return table


def add_minor_dignities_table(document: Document, observation: Observation):
    """Table des dignités mineures (triplicité, bornes égyptiennes, décans) —
    séparée de la table des positions, qui correspond exactement au tableau
    des documents de référence (lesquels ne couvrent pas ces dignités)."""
    table = document.add_table(rows=1, cols=len(MINOR_DIGNITIES_HEADER))
    for cell, text in zip(table.rows[0].cells, MINOR_DIGNITIES_HEADER):
        styles.set_header_cell(cell, text)
    styles.style_table(table, MINOR_DIGNITIES_COLUMN_WIDTHS_DXA)

    for planet in observation.planets:
        cells = table.add_row().cells
        cells[0].text = planet.name
        cells[1].text = planet.triplicity_dignity or "—"
        cells[2].text = planet.bound_dignity or "—"
        cells[3].text = planet.decan_dignity or "—"
    return table


def format_releasing_date(when: datetime) -> str:
    return when.strftime("%d/%m/%Y")


def _zodiacal_releasing_row(
    table, period: ReleasingPeriod, level_label: str, fortune_sign: str
) -> None:
    cells = table.add_row().cells
    cells[0].text = level_label
    cells[1].text = period.sign
    cells[2].text = period.ruler
    cells[3].text = format_releasing_date(period.start)
    cells[4].text = format_releasing_date(period.end)
    # Toujours par rapport à la Part de Fortune, même dans la table de
    # l'Esprit (confirmé par une source primaire, voir zodiacal_releasing.is_peak_period).
    cells[5].text = "Oui" if is_peak_period(period, fortune_sign) else "—"


def add_zodiacal_releasing_table(
    document: Document, chapters: list[ReleasingChapter], fortune_sign: str
):
    """Table des chapitres (L1) et sous-périodes (L2) de libération
    zodiacale. `fortune_sign` sert uniquement au marquage des périodes
    culminantes ; les périodes elles-mêmes sont déjà calculées (Fortune ou
    Esprit) en amont dans `core.chart`."""
    table = document.add_table(rows=1, cols=len(ZODIACAL_RELEASING_HEADER))
    for cell, text in zip(table.rows[0].cells, ZODIACAL_RELEASING_HEADER):
        styles.set_header_cell(cell, text)
    styles.style_table(table, ZODIACAL_RELEASING_COLUMN_WIDTHS_DXA)

    for chapter in chapters:
        _zodiacal_releasing_row(table, chapter.l1, "L1", fortune_sign)
        for sub in chapter.sub_periods:
            _zodiacal_releasing_row(table, sub, "L2", fortune_sign)
    return table


def _display_name(name: str) -> str:
    return DISPLAY_NAME_WITH_ARTICLE.get(name, name)


def _join_french(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " et " + names[-1]


def conjunction_text(cluster: SignCluster) -> str | None:
    """Puce de conjonction pour un amas d'au moins deux membres.

    Renvoie None pour un amas à un seul membre (rien à conjoindre).
    """
    if len(cluster.members) < 2:
        return None
    names = _join_french([_display_name(m) for m in cluster.members])
    verb = "conjointes" if all(m in FEMININE_POINTS for m in cluster.members) else "conjoints"
    return f"{names} {verb} en {cluster.sign} (maison {cluster.house})."


def cluster_aspect_text(cluster_aspect: ClusterAspect, clusters_by_sign: dict[str, SignCluster]) -> str:
    cluster_a = clusters_by_sign[cluster_aspect.sign_a]
    cluster_b = clusters_by_sign[cluster_aspect.sign_b]
    if cluster_aspect.boundary_exception:
        return (
            f"{cluster_a.sign} (maison {cluster_a.house}) et {cluster_b.sign} "
            f"(maison {cluster_b.house}) : conjonction hors signe "
            "(règle des 3°, signes adjacents)."
        )
    label = ASPECT_LABEL[cluster_aspect.aspect]
    return (
        f"{cluster_a.sign} (maison {cluster_a.house}) en {label} avec "
        f"{cluster_b.sign} (maison {cluster_b.house})."
    )


def mutual_reception_text(reception: MutualReception) -> str:
    return f"Réception mutuelle par domicile entre {reception.planet_a} et {reception.planet_b}."


def add_aspects_section(document: Document, observation: Observation) -> None:
    """Puces factuelles des aspects par signe : conjonctions intra-amas,
    relation d'aspect (ou aversion) pour chaque paire d'amas, puis les
    réceptions mutuelles par domicile (un lien technique indépendant des
    aspects, placé ici comme dans les documents de référence).

    Le commentaire interprétatif (ex. significations de maîtrise) reste hors
    périmètre de docgen : c'est une tâche de rédaction, pas de calcul.
    """
    for cluster in observation.clusters:
        text = conjunction_text(cluster)
        if text:
            document.add_paragraph(text, style="List Bullet")

    clusters_by_sign = {cluster.sign: cluster for cluster in observation.clusters}
    for cluster_aspect in observation.cluster_aspects:
        document.add_paragraph(
            cluster_aspect_text(cluster_aspect, clusters_by_sign), style="List Bullet"
        )

    for reception in observation.mutual_receptions:
        document.add_paragraph(mutual_reception_text(reception), style="List Bullet")


def _distribution_points(observation: Observation) -> list[PointPosition]:
    """Le jeu de points utilisé pour la répartition élémentaire/modale et
    l'angularité (Phase 2) : Ascendant + 7 planètes + Nœud Nord + les 3
    Parts, à l'exclusion du Milieu du Ciel et du Nœud Sud. Convention déduite
    par inspection croisée des deux documents de référence, qui l'appliquent
    tous les deux identiquement sans jamais l'expliciter."""
    excluded = {"Milieu du Ciel", "Nœud Sud"}
    return [p for p in observation.all_points if p.name not in excluded]


def add_elemental_modal_section(document: Document, observation: Observation) -> None:
    """Répartition élémentaire (Ascendant/Soleil/Lune) et modale (les 12
    points de `_distribution_points`), en Phase 2.

    Rendu volontairement plus simple, en style « libellé technique », que la
    prose des documents de référence (qui emploie un jugement qualitatif —
    « dominante fixe », « suivie de près par » — ne généralisant pas
    proprement à un comptage arbitraire, et une accord grammatical
    singulier/pluriel qui ajouterait de la fragilité pour peu de gain) :
    même choix que le jalon 4 pour les puces d'aspects.
    """
    points = _distribution_points(observation)
    main_points = [observation.ascendant, observation.planet("Soleil"), observation.planet("Lune")]
    main_names = {"Ascendant", "Soleil", "Lune"}

    # Liste à virgules simples (pas de "et" final) : convention des documents
    # de référence pour ce type d'énumération positionnelle, distincte de la
    # jonction "et" utilisée par _join_french pour les puces d'aspects.
    main_elements_text = ", ".join(
        f"{p.name} en {p.element.lower()} ({p.sign})" for p in main_points
    )
    present_among_main = {p.element for p in main_points}
    missing_elements = sorted({"Feu", "Terre", "Air", "Eau"} - present_among_main)
    other_points = [p for p in points if p.name not in main_names]
    elements_elsewhere = {p.element for p in other_points}
    present_elsewhere = [e for e in missing_elements if e in elements_elsewhere]
    absent_entirely = [e for e in missing_elements if e not in elements_elsewhere]

    def _lower_list(elements: list[str]) -> str:
        return _join_french([e.lower() for e in elements]) if elements else "aucun"

    document.add_paragraph(
        f"Éléments des trois points directeurs : {main_elements_text}. "
        f"Éléments absents de ces trois points : {_lower_list(missing_elements)}. "
        f"Présents ailleurs dans le thème : {_lower_list(present_elsewhere)}. "
        f"Absents de l'ensemble du thème : {_lower_list(absent_entirely)}."
    )

    modality_groups: dict[str, list[PointPosition]] = {"Cardinal": [], "Fixe": [], "Mutable": []}
    for p in points:
        modality_groups[p.modality].append(p)
    ordered_modalities = sorted(modality_groups.items(), key=lambda kv: -len(kv[1]))

    modality_sentences = []
    for modality, members in ordered_modalities:
        count = len(members)
        names = _join_french([p.name for p in members]) if members else "aucun facteur"
        modality_sentences.append(f"{modality} : {names} ({count} facteur{'s' if count != 1 else ''}).")
    document.add_paragraph(
        "Modalité, par ordre décroissant de nombre de facteurs : " + " ".join(modality_sentences)
    )


def add_angularity_section(document: Document, observation: Observation) -> None:
    """Angularité (maisons angulaires 1/4/7/10) des 12 points de
    `_distribution_points`, en Phase 2. Structure identique dans les deux
    documents de référence, reproduite fidèlement — à l'exception du nom
    complet « le Soleil » employé une fois dans le document de Liam, non
    repris ici : incohérent avec la convention déjà établie et testée en
    Phase 1 (`DISPLAY_NAME_WITH_ARTICLE`), qui n'ajoute pas d'article aux
    luminaires/planètes.
    """
    points = _distribution_points(observation)
    by_house: dict[int, list[PointPosition]] = {}
    for p in points:
        by_house.setdefault(p.house, []).append(p)

    angular_sentences = [
        f"Maison {house} : {', '.join(p.name for p in by_house[house])}."
        for house in (1, 4, 7, 10)
        if by_house.get(house)
    ]
    document.add_paragraph(" ".join(angular_sentences))

    non_angular_houses = [h for h in by_house if h not in (1, 4, 7, 10)]
    if non_angular_houses:
        groups = [
            f"{_join_french([_display_name(p.name) for p in by_house[house]])} "
            f"(maison {house}, {house_quality(house).lower()})"
            for house in non_angular_houses
        ]
        document.add_paragraph("Hors angularité : " + ", ".join(groups) + ".")


def build_observation_document(observation: Observation) -> Document:
    """Construit le document .docx : Phase 1 (Observation) complète, et les
    sous-sections de Phase 2 (Fiche technique) déjà couvertes par docgen
    (voir CLAUDE.md pour l'état d'avancement exact).

    Phase 3 (Interprétation) et le reste de la Phase 2 impliquent une
    rédaction descriptive qui dépasse encore le périmètre de docgen : docgen
    ne fait que mettre en forme des données déjà calculées.
    """
    document = Document()
    document.add_heading("Phase 1 — Observation", level=1)

    document.add_heading("Positions planétaires et facteurs sensibles", level=2)
    add_positions_table(document, observation)

    document.add_heading(
        "Maîtrises traditionnelles (règle de rulership unique par planète)", level=2
    )
    add_rulerships_table(document, observation)

    document.add_heading("Dignités mineures (triplicité, bornes, décans)", level=2)
    add_minor_dignities_table(document, observation)

    document.add_heading("Aspects par signe relevés", level=2)
    add_aspects_section(document, observation)

    fortune_sign = observation.part_of_fortune.sign
    document.add_heading("Libération zodiacale — Part de Fortune", level=2)
    add_zodiacal_releasing_table(document, observation.zodiacal_releasing_fortune, fortune_sign)

    document.add_heading("Libération zodiacale — Part de l'Esprit", level=2)
    add_zodiacal_releasing_table(document, observation.zodiacal_releasing_spirit, fortune_sign)

    document.add_heading("Phase 2 — Fiche technique", level=1)

    document.add_heading("Répartition élémentaire et modale", level=2)
    add_elemental_modal_section(document, observation)

    document.add_heading("Angularité", level=2)
    add_angularity_section(document, observation)

    return document
