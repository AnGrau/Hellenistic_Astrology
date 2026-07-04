from docx import Document

from ..core.aspects import ClusterAspect, SignCluster
from ..core.observation import Observation, PointPosition
from . import styles

FEMININE_PLANETS = {"Lune", "Vénus"}
FEMININE_POINTS = FEMININE_PLANETS | {"Part de Fortune", "Part de l'Esprit"}

# Noms affichés avec article, pour les puces d'aspects (les planètes
# s'affichent sans article, comme dans les documents de référence).
DISPLAY_NAME_WITH_ARTICLE = {
    "Ascendant": "l'Ascendant",
    "Milieu du Ciel": "le Milieu du Ciel",
    "Part de Fortune": "la Part de Fortune",
    "Part de l'Esprit": "la Part de l'Esprit",
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

    points = [
        observation.ascendant,
        *observation.planets,
        observation.midheaven,
        observation.part_of_fortune,
        observation.part_of_spirit,
    ]
    for point in points:
        if point is not None:
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


def add_aspects_section(document: Document, observation: Observation) -> None:
    """Puces factuelles des aspects par signe : conjonctions intra-amas puis
    relation d'aspect (ou aversion) pour chaque paire d'amas.

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

    document.add_heading("Aspects par signe relevés", level=2)
    add_aspects_section(document, observation)

    return document
