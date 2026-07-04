"""Génère un .docx de la phase 1 (Observation) pour un des deux cas de test locaux.

Usage : uv run python scripts/generate_docx.py anthony
Écrit dans output/<nom>.docx (gitignored : contient des données de naissance).

Pour un nouveau client (au-delà d'Anthony/Liam), utiliser plutôt le CLI
général : `uv run hellenistic-astrology <fichier-birth-data.json>`.
"""

import json
import sys
from pathlib import Path

from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.timezone import birth_data_from_dict
from hellenistic_astrology.docgen.builder import build_observation_document

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage : uv run python scripts/generate_docx.py <nom-fixture>")
        raise SystemExit(1)

    name = sys.argv[1]
    with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
        fixture = json.load(f)

    birth = birth_data_from_dict(fixture["birth_data"])
    observation = build_observation(birth)
    document = build_observation_document(observation)

    OUTPUT_DIR.mkdir(exist_ok=True)
    target = OUTPUT_DIR / f"{name}.docx"
    document.save(target)
    print(f"écrit : {target}")


if __name__ == "__main__":
    main()
