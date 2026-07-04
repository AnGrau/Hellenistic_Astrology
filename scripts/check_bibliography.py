"""Vérifie que les URLs bibliographiques de CLAUDE.md sont toujours valides.

CLAUDE.md exige de revérifier ces URLs avant chaque publication plutôt que
de les recopier sans contrôle (elles pointent vers des pages officielles
d'éditeur/autrice, susceptibles de changer).

Usage : uv run python scripts/check_bibliography.py
Code de sortie non nul si au moins une URL échoue.
"""

import sys

from hellenistic_astrology.bibliography import check_all


def main() -> int:
    results = check_all()
    all_ok = True
    for result in results:
        status = "OK" if result.ok else "ÉCHEC"
        print(f"[{status}] {result.label}\n       {result.url} ({result.detail})")
        if not result.ok:
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
