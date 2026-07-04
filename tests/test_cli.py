import json

from docx import Document

from hellenistic_astrology.cli import main, slugify

from .regression_helpers import load_fixture


def test_slugify_strips_accents_and_spaces():
    assert slugify("Anthony") == "anthony"
    assert slugify("Éloïse Dupont-Martin") == "eloise-dupont-martin"
    assert slugify("   ") == "theme"


def test_cli_generates_docx_from_json_birth_data(tmp_path):
    fixture = load_fixture("anthony")
    birth_data_path = tmp_path / "anthony.json"
    birth_data_path.write_text(json.dumps(fixture["birth_data"]), encoding="utf-8")

    output_path = tmp_path / "rapport.docx"
    exit_code = main([str(birth_data_path), "-o", str(output_path)])

    assert exit_code == 0
    assert output_path.exists()

    document = Document(str(output_path))
    headings = [p.text for p in document.paragraphs if p.style.name == "Heading 1"]
    assert headings == ["Table des matières", "Phase 1 — Observation", "Phase 2 — Fiche technique"]


def test_cli_defaults_output_to_output_dir_with_slugified_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fixture = load_fixture("liam")
    birth_data_path = tmp_path / "liam.json"
    birth_data_path.write_text(json.dumps(fixture["birth_data"]), encoding="utf-8")

    exit_code = main([str(birth_data_path)])

    assert exit_code == 0
    assert (tmp_path / "output" / "liam.docx").exists()
