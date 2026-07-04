"""Assemble un brief factuel pour la rédaction assistée de la Phase 3 —
Interprétation.

Ce module ne génère aucune prose interprétative lui-même (voir CLAUDE.md,
jalon 26, pour la décision de mécanisme : brief déterministe et testé, pas
d'appel API automatisé dans le pipeline — la rédaction reste une étape
assistée/supervisée, hors CLI). Il réutilise les faits déjà produits et
testés par `docgen.builder` (Phase 1/2) pour les sous-sections qui leur
correspondent, et n'ajoute que les quelques faits propres à la Phase 3 (la
période de libération zodiacale active à la date de génération, la
précision de l'heure de naissance).

La sortie est du texte brut/Markdown portable : utilisable tel quel dans
Claude Chat, Claude Code ou Mistral Vibe/Le Chat, sans dépendre d'un accès
à CLAUDE.md (les règles de style pertinentes sont rappelées en tête).
"""

from datetime import datetime, timezone

from docx import Document

from .. import bibliography
from ..core.observation import Observation
from ..core.timezone import BirthData
from ..core.zodiacal_releasing import active_period
from ..docgen.builder import (
    add_angularity_section,
    add_ascendant_and_ruler_section,
    add_aspects_section,
    add_dignities_and_receptions_section,
    add_elemental_modal_section,
    add_luminaries_section,
    format_releasing_date,
)

STYLE_REMINDER = (
    "Règles de style (CLAUDE.md) à respecter dans la rédaction :\n"
    "- Ton bienveillant mais factuel, jamais péremptoire sur la vie de la "
    "personne (formulations du type « invite à », « suggère », « mérite "
    "d'être vérifié avec la personne concernée »).\n"
    "- Aucune émoticône.\n"
    "- Toute affirmation technique (dignité, aspect, secte) doit rester "
    "vérifiable depuis les faits ci-dessous — pas d'interprétation qui "
    "devance les faits.\n"
    "- Bibliographie systématique en fin de document (liste fournie en bas "
    "de ce brief)."
)

# Identique mot pour mot dans les deux documents de référence.
INTRO_TEXT = (
    "Cette section relie les observations entre elles pour proposer une "
    "lecture d'ensemble. Comme toute délinéation, elle gagne à être "
    "vérifiée et affinée lors d'un échange direct avec la personne "
    "concernée."
)

LIMITATIONS_INTRO = (
    "Cette lecture applique strictement les réglages indiqués (maisons en "
    "signes entiers, zodiaque tropical, aspects ptoléméens par signe, "
    "règle des 3° pour les aspects hors-signe)."
)

LIMITATIONS_CLOSING = (
    "Ce document constitue une base de travail fidèle à la méthode ; il "
    "gagnera, comme tout thème, à être discuté avec la personne concernée "
    "pour vérifier comment ces structures se traduisent concrètement dans "
    "son parcours."
)

SYNTHESIS_PROMPT = (
    "Aucun fait nouveau ici : synthétiser les points saillants des sections "
    "précédentes (orientation générale, Ascendant/maître, luminaires, "
    "structure du thème, nuances de secte/dignité) en une conclusion brève "
    "et cohérente."
)


def _section_facts(*section_fns, observation: Observation) -> str:
    """Rejoue une ou plusieurs fonctions `add_*_section` de `docgen.builder`
    contre un document jetable et renvoie le texte des paragraphes produits
    — même faits que la Phase 2, aucune divergence possible."""
    document = Document()
    for fn in section_fns:
        fn(document, observation)
    return "\n".join(p.text for p in document.paragraphs if p.text)


def _sect_roles_by_planet(observation: Observation) -> str:
    """Rôle de secte par planète (`PointPosition.sect_role`) : déjà calculé
    et déjà affiché dans la table des positions (Phase 1), mais pas encore
    listé isolément ailleurs — utile tel quel pour "Nuances de secte"."""
    return "\n".join(f"{p.name} : {p.sect_role}" for p in observation.planets)


def _current_releasing_periods(observation: Observation, when: datetime) -> str:
    """Période de libération zodiacale active à `when` (niveaux L1 et L2),
    pour la Part de Fortune et la Part de l'Esprit — réutilise
    `zodiacal_releasing.active_period`, déjà testé (jalon 17), sur les
    chapitres déjà calculés jusqu'à 100 ans (jalon 18)."""
    lines = []
    for label, chapters in (
        ("Part de Fortune", observation.zodiacal_releasing_fortune),
        ("Part de l'Esprit", observation.zodiacal_releasing_spirit),
    ):
        flat = [chapter.l1 for chapter in chapters] + [
            sub for chapter in chapters for sub in chapter.sub_periods
        ]
        l1 = active_period(flat, 1, when)
        l2 = active_period(flat, 2, when)
        if l1 is None:
            lines.append(f"{label} : aucune période active à cette date (hors horizon calculé).")
            continue
        lines.append(
            f"{label} : période majeure (L1) en {l1.sign} (maître {l1.ruler}) du "
            f"{format_releasing_date(l1.start)} au {format_releasing_date(l1.end)}."
        )
        if l2 is not None:
            lines.append(
                f"  Sous-période (L2) en {l2.sign} (maître {l2.ruler}) du "
                f"{format_releasing_date(l2.start)} au {format_releasing_date(l2.end)}."
            )
    return "\n".join(lines)


def _birth_time_precision_clause(birth: BirthData) -> str:
    if birth.local_time is not None:
        formatted = f"{birth.local_time.hour}h{birth.local_time.minute:02d}"
        return (
            f"L'heure de naissance fournie ({formatted}) est précise à la "
            "minute, ce qui est suffisant pour asseoir l'Ascendant et le "
            "Milieu du Ciel avec confiance dans ce système de maisons."
        )
    return (
        "La naissance a été renseignée directement en heure UTC (sans "
        "heure locale explicite) : vérifier que la précision de cette "
        "donnée reste suffisante pour asseoir l'Ascendant et le Milieu du "
        "Ciel avec confiance dans ce système de maisons."
    )


def build_interpretation_brief(
    observation: Observation, birth: BirthData, when: datetime | None = None
) -> str:
    """Brief factuel pour la rédaction assistée des 8 sous-sections réelles
    de Phase 3 (voir CLAUDE.md, jalon 26). `when` : date de référence pour
    "Repères temporels actuels" (par défaut, l'instant de génération).
    """
    # `resolve_utc` (core.timezone) renvoie des datetimes UTC *avec*
    # fuseau (timezone.utc) — les périodes de libération zodiacale en
    # héritent, donc `when` doit être comparable (tz-aware), pas naïf.
    when = when or datetime.now(timezone.utc)

    sections = [
        ("Intro (sans titre dans les documents de référence)", INTRO_TEXT),
        (
            "Orientation générale",
            _section_facts(add_elemental_modal_section, add_angularity_section, observation=observation),
        ),
        (
            "L'Ascendant et son maître",
            _section_facts(add_ascendant_and_ruler_section, observation=observation),
        ),
        ("Les luminaires", _section_facts(add_luminaries_section, observation=observation)),
        ("La structure du thème", _section_facts(add_aspects_section, observation=observation)),
        (
            "Nuances de secte, de dignité (et de mouvement)",
            _section_facts(add_dignities_and_receptions_section, observation=observation)
            + "\n\nRôle de secte par planète :\n"
            + _sect_roles_by_planet(observation),
        ),
        ("Synthèse", SYNTHESIS_PROMPT),
        ("Repères temporels actuels", _current_releasing_periods(observation, when)),
        (
            "Limites de cette analyse",
            LIMITATIONS_INTRO + "\n" + _birth_time_precision_clause(birth) + "\n" + LIMITATIONS_CLOSING,
        ),
    ]

    lines = [
        f"# Brief de rédaction — Phase 3 — Interprétation — {observation.name}",
        "",
        STYLE_REMINDER,
        "",
    ]
    for title, content in sections:
        lines.append(f"## {title}")
        lines.append(content)
        lines.append("")

    lines.append("## Bibliographie à inclure en fin de document")
    for label, url in bibliography.REFERENCES:
        lines.append(f"- {label} — {url}")

    return "\n".join(lines)
