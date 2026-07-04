"""Assemble le document final : ajoute la prose de Phase 3 (déjà rédigée
et finalisée) à la suite d'un .docx de Phase 1/2 déjà généré.

Usage : uv run python scripts/assemble_document.py <fichier.docx> <fichier.md> [-o sortie.docx]

Contrairement à generate_docx.py/generate_brief.py, ne prend pas un nom de
fixture : les entrées sont deux fichiers déjà produits (n'importe quel
thème), pas des données de naissance.
"""

import argparse
import sys

from hellenistic_astrology.assembly import assemble_final_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assemble_document.py",
        description=__doc__,
    )
    parser.add_argument("docx_path", help="Document .docx de Phase 1/2 déjà généré.")
    parser.add_argument("markdown_path", help="Texte de Phase 3 déjà rédigé et finalisé (Markdown).")
    parser.add_argument(
        "-o", "--output", default=None, help="Chemin du .docx final (défaut : <docx_path>_final.docx)."
    )
    args = parser.parse_args(argv)

    try:
        target = assemble_final_document(args.docx_path, args.markdown_path, args.output)
    except ValueError as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1

    print(f"écrit : {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
