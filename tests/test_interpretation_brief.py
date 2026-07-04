from datetime import datetime, time, timezone

import pytest

from hellenistic_astrology.core.chart import build_observation
from hellenistic_astrology.core.timezone import BirthData
from hellenistic_astrology.core.zodiacal_releasing import ReleasingChapter, ReleasingPeriod
from hellenistic_astrology.interpretation.brief import (
    STYLE_REMINDER,
    _birth_time_precision_clause,
    _current_releasing_periods,
    build_interpretation_brief,
)

from .regression_helpers import birth_data_from_fixture, load_fixture

EXPECTED_HEADINGS = [
    "## Intro (sans titre dans les documents de référence)",
    "## Orientation générale",
    "## L'Ascendant et son maître",
    "## Les luminaires",
    "## La structure du thème",
    "## Nuances de secte, de dignité (et de mouvement)",
    "## Synthèse",
    "## Repères temporels actuels",
    "## Limites de cette analyse",
    "## Bibliographie à inclure en fin de document",
]


@pytest.mark.parametrize("fixture_name", ["anthony", "liam"])
def test_build_interpretation_brief_contains_all_sections(fixture_name):
    fixture = load_fixture(fixture_name)
    birth = birth_data_from_fixture(fixture)
    observation = build_observation(birth)

    brief = build_interpretation_brief(observation, birth)

    assert brief.startswith(f"# Brief de rédaction — Phase 3 — Interprétation — {fixture_name.capitalize()}")
    assert STYLE_REMINDER in brief
    for heading in EXPECTED_HEADINGS:
        assert heading in brief
    # Les 4 références bibliographiques (jalon 10) doivent être présentes.
    assert "https://theastrologypodcast.com/books/" in brief
    assert "https://rubedo.press/ancient-astrology-volume-two" in brief


def test_build_interpretation_brief_reuses_phase2_facts_verbatim():
    # Recoupe un fait Phase 1/2 déjà validé (jalon 20 : écarts au Soleil
    # exacts d'Anthony) pour confirmer que le brief rejoue bien les mêmes
    # fonctions add_*_section plutôt que de recalculer séparément.
    fixture = load_fixture("anthony")
    birth = birth_data_from_fixture(fixture)
    observation = build_observation(birth)

    brief = build_interpretation_brief(observation, birth)

    assert "Mercure (13°46' d'écart) et Jupiter (9°09' d'écart)" in brief
    assert "Réception mutuelle par domicile entre Vénus et Mars." in brief


def test_build_interpretation_brief_lists_sect_role_per_planet():
    fixture = load_fixture("liam")
    birth = birth_data_from_fixture(fixture)
    observation = build_observation(birth)

    brief = build_interpretation_brief(observation, birth)

    assert "Rôle de secte par planète :" in brief
    assert "Soleil : Lumière de secte" in brief
    assert "Saturne : Maléfique de secte" in brief


def test_birth_time_precision_clause_with_local_time():
    birth = BirthData(name="Test", local_time=time(23, 10))
    clause = _birth_time_precision_clause(birth)
    assert "23h10" in clause
    assert "précise à la minute" in clause


def test_birth_time_precision_clause_utc_only_fallback():
    birth = BirthData(name="Test", utc_datetime=datetime(1970, 11, 20, 22, 10, tzinfo=timezone.utc))
    clause = _birth_time_precision_clause(birth)
    assert "heure locale explicite" in clause
    assert "vérifier" in clause


def test_current_releasing_periods_active_l1_and_l2():
    l1 = ReleasingPeriod(
        level=1, sign="Lion", ruler="Soleil",
        start=datetime(2020, 1, 1, tzinfo=timezone.utc), end=datetime(2039, 1, 1, tzinfo=timezone.utc),
    )
    l2 = ReleasingPeriod(
        level=2, sign="Vierge", ruler="Mercure",
        start=datetime(2025, 1, 1, tzinfo=timezone.utc), end=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    chapters = [ReleasingChapter(l1=l1, sub_periods=[l2])]

    class FakeObservation:
        zodiacal_releasing_fortune = chapters
        zodiacal_releasing_spirit = chapters

    text = _current_releasing_periods(FakeObservation(), when=datetime(2026, 6, 1, tzinfo=timezone.utc))

    assert "Part de Fortune : période majeure (L1) en Lion (maître Soleil) du 01/01/2020 au 01/01/2039." in text
    assert "Sous-période (L2) en Vierge (maître Mercure) du 01/01/2025 au 01/01/2027." in text
    assert text.count("Part de l'Esprit") == 1


def test_current_releasing_periods_outside_horizon():
    l1 = ReleasingPeriod(
        level=1, sign="Lion", ruler="Soleil",
        start=datetime(2020, 1, 1, tzinfo=timezone.utc), end=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    chapters = [ReleasingChapter(l1=l1, sub_periods=[])]

    class FakeObservation:
        zodiacal_releasing_fortune = chapters
        zodiacal_releasing_spirit = chapters

    text = _current_releasing_periods(FakeObservation(), when=datetime(2030, 1, 1, tzinfo=timezone.utc))

    assert "aucune période active à cette date (hors horizon calculé)." in text
