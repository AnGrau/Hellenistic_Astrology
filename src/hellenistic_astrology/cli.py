import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

from .core.chart import build_observation
from .core.timezone import birth_data_from_dict
from .docgen.builder import build_observation_document


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.strip().lower()).strip("-")
    return slug or "theme"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hellenistic-astrology",
        description=(
            "Génère la Phase 1 (Observation) d'un thème natal hellénistique en .docx, "
            "à partir d'un fichier JSON de données de naissance."
        ),
    )
    parser.add_argument(
        "birth_data_json",
        type=Path,
        help=(
            "Fichier JSON : name, latitude, longitude, local_date, local_time, tz_name "
            "(ou utc_datetime à la place de local_date/local_time/tz_name pour les dates "
            "antérieures à 1916)."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Chemin du .docx généré (défaut : output/<nom>.docx).",
    )
    args = parser.parse_args(argv)

    with args.birth_data_json.open(encoding="utf-8") as f:
        data = json.load(f)

    birth = birth_data_from_dict(data)
    observation = build_observation(birth)
    document = build_observation_document(observation)

    output_path = args.output or Path("output") / f"{slugify(birth.name)}.docx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    print(f"écrit : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
