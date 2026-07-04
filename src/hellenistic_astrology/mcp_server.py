"""Serveur MCP local (stdio) exposant le calcul de thème (Phase 1/2) et le
brief de Phase 3 (jalon 26) à Claude Code et Mistral Vibe, quand ils
travaillent sur ce dépôt cloné.

Transport stdio uniquement (sous-processus local, aucune exposition
réseau) : structurellement identique, du point de vue de la licence
AGPL-3.0 de pyswisseph, à l'exécution du CLI en local — pas de nouveau
problème de licence (voir CLAUDE.md). Un serveur MCP distant/hébergé
publiquement est un chantier volontairement hors périmètre ici (il
déclencherait la clause de licence Swiss Ephemeris Professional déjà
actée dans CLAUDE.md).

Chaque outil est une fine couche `@mcp.tool()` au-dessus d'une fonction
Python nue et testable sans dépendre du SDK MCP — voir les fonctions
`_*` ci-dessous, couvertes par `tests/test_mcp_server.py`.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .cli import slugify
from .core.chart import build_observation
from .core.geocoding import GeocodingError
from .core.timezone import birth_data_from_dict
from .docgen.builder import build_observation_document
from .interpretation.brief import build_interpretation_brief

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"

mcp = FastMCP("hellenistic-astrology")


def _compute_observation_json(birth_data: dict) -> str:
    """Calcule l'Observation (Phase 1/2) et la renvoie en JSON structuré,
    sans passer par un .docx — réutilise `Observation.to_json`, déjà
    existante mais jusqu'ici jamais exposée en dehors des tests."""
    birth = birth_data_from_dict(birth_data)
    observation = build_observation(birth)
    return observation.to_json(indent=2)


def _generate_document(birth_data: dict, output_path: str | None = None) -> str:
    """Génère le .docx (Phase 1/2 complètes) — même logique que le CLI
    (`cli.main`), réutilise `cli.slugify` pour le nom par défaut."""
    birth = birth_data_from_dict(birth_data)
    observation = build_observation(birth)
    document = build_observation_document(observation)

    target = Path(output_path) if output_path else OUTPUT_DIR / f"{slugify(birth.name)}.docx"
    target.parent.mkdir(parents=True, exist_ok=True)
    document.save(target)
    return f"écrit : {target}"


def _generate_interpretation_brief(birth_data: dict) -> str:
    """Génère le brief factuel de Phase 3 (jalon 26) — écrit aussi dans
    output/ par cohérence avec `scripts/generate_brief.py`, et renvoie le
    texte directement pour un enchaînement immédiat (ex. avec le skill de
    rédaction du jalon 27)."""
    birth = birth_data_from_dict(birth_data)
    observation = build_observation(birth)
    brief = build_interpretation_brief(observation, birth)

    target = OUTPUT_DIR / f"{slugify(birth.name)}_brief.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(brief, encoding="utf-8")
    return brief


def _with_error_handling(fn, *args) -> str:
    try:
        return fn(*args)
    except (GeocodingError, ValueError) as exc:
        return f"erreur : {exc}"


@mcp.tool()
def compute_observation(birth_data: dict) -> str:
    """Calcule les positions, maisons, secte, dignités, aspects, Lots et
    libération zodiacale (Phase 1/2) d'un thème natal hellénistique, et
    renvoie le résultat en JSON structuré. `birth_data` suit le même schéma
    que le JSON attendu par le CLI (name, latitude+longitude ou place,
    local_date+local_time+tz_name ou utc_datetime)."""
    return _with_error_handling(_compute_observation_json, birth_data)


@mcp.tool()
def generate_document(birth_data: dict, output_path: str | None = None) -> str:
    """Génère le document .docx complet (Phase 1 + Phase 2) pour un thème
    natal hellénistique et l'écrit sur disque (défaut : output/<nom>.docx).
    Renvoie le chemin écrit."""
    return _with_error_handling(_generate_document, birth_data, output_path)


@mcp.tool()
def generate_interpretation_brief(birth_data: dict) -> str:
    """Génère le brief factuel de rédaction assistée pour la Phase 3
    (Interprétation) d'un thème natal hellénistique — à utiliser avec le
    skill `hellenistic-astrology-phase3` pour rédiger le texte final."""
    return _with_error_handling(_generate_interpretation_brief, birth_data)


if __name__ == "__main__":
    mcp.run()
