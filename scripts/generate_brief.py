"""Génère le brief de rédaction assistée (Phase 3) pour un des deux cas de
test locaux.

Usage : uv run python scripts/generate_brief.py anthony
Écrit dans output/<nom>_brief.md (gitignored : contient des données de naissance).

Ce brief est un socle factuel déterministe, pas de la prose interprétative :
voir CLAUDE.md (jalon 26) pour la décision de mécanisme (rédaction assistée,
hors CLI, pas d'appel API automatisé).
"""

import json
import sys
from pathlib import Path

from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.timezone import birth_data_from_dict
from hellenistic_astrology.interpretation.brief import build_interpretation_brief

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage : uv run python scripts/generate_brief.py <nom-fixture>")
        raise SystemExit(1)

    name = sys.argv[1]
    with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
        fixture = json.load(f)

    birth = birth_data_from_dict(fixture["birth_data"])
    observation = build_observation(birth)
    brief = build_interpretation_brief(observation, birth)

    OUTPUT_DIR.mkdir(exist_ok=True)
    target = OUTPUT_DIR / f"{name}_brief.md"
    target.write_text(brief, encoding="utf-8")
    print(f"écrit : {target}")


if __name__ == "__main__":
    main()
