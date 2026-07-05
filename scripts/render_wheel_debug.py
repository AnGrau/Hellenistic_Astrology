"""Rendu rapide de la seule roue du thème (PNG), pour itérer sur les
paramètres visuels de `docgen/chart_image.py` sans régénérer tout le
`.docx`.

Usage : uv run python scripts/render_wheel_debug.py anthony [nom_sortie]
Écrit dans output/wheel_debug/<nom_sortie ou nom-fixture>.png (gitignored,
sous-dossier de output/).
"""

import json
import sys
from pathlib import Path

from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.timezone import birth_data_from_dict
from hellenistic_astrology.docgen.chart_image import render_chart_wheel

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output" / "wheel_debug"


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print("Usage : uv run python scripts/render_wheel_debug.py <nom-fixture> [nom_sortie]")
        raise SystemExit(1)

    name = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) == 3 else name

    with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
        fixture = json.load(f)

    birth = birth_data_from_dict(fixture["birth_data"])
    observation = build_observation(birth)
    png = render_chart_wheel(observation)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / f"{output_name}.png"
    target.write_bytes(png)
    print(f"écrit : {target}")


if __name__ == "__main__":
    main()
