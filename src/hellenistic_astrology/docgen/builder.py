from docx import Document

from ..core.observation import Observation, PointPosition
from . import styles

FEMININE_PLANETS = {"Lune", "Vénus"}

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

    return document
