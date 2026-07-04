from datetime import datetime

from docx import Document

from ..core.aspects import ClusterAspect, SignCluster
from ..core.dignities import MutualReception
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


def build_observation_document(observation: Observation) -> Document:
    """Construit le document .docx pour la Phase 1 (Observation) uniquement.

    Les phases 2 (fiche technique) et 3 (interprétation) impliquent une
    rédaction descriptive qui dépasse le périmètre de docgen : docgen ne
    fait que mettre en forme des données déjà calculées.
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

    return document
