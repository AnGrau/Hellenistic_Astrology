from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Twips

HEADER_SHADING = "EDE6F0"
FONT_NAME = "Calibri"
HEADER_FONT_SIZE_PT = 10


def shade_cell(cell, color_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def set_header_cell(cell, text: str) -> None:
    cell.text = text
    shade_cell(cell, HEADER_SHADING)
    run = cell.paragraphs[0].runs[0]
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = Pt(HEADER_FONT_SIZE_PT)


def style_table(table, column_widths_dxa: list[int]) -> None:
    table.style = "Table Grid"
    table.autofit = False
    for row in table.rows:
        for cell, width in zip(row.cells, column_widths_dxa):
            cell.width = Twips(width)
