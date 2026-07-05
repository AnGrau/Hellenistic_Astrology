from hellenistic_astrology.core import ephemeris
from hellenistic_astrology.core.chart import DEFAULT_EPHE_PATH, build_observation
from hellenistic_astrology.core.phasis import (
    PHASIS_WINDOW_DAYS,
    _DailySample,
    _find_crossings,
    _heliacal_label,
    _nearest_event,
    _station_label,
    compute_phasis_events,
)

from .regression_helpers import birth_data_from_fixture, load_fixture

_KNOWN_EVENT_TYPES = {
    "Station directe",
    "Station rétrograde",
    "Lever héliaque du matin",
    "Coucher héliaque du matin",
    "Lever héliaque du soir",
    "Coucher héliaque du soir",
}


def _sample(day_offset: int, speed: float = 1.0, gap_to_sun: float = 90.0, west_of_sun: bool = True) -> _DailySample:
    return _DailySample(day_offset=day_offset, speed=speed, gap_to_sun=gap_to_sun, west_of_sun=west_of_sun)


# ---------------------------------------------------------------------------
# Logique pure : stations
# ---------------------------------------------------------------------------


def test_station_label_retrograde_and_direct():
    assert _station_label(speed_before=0.5, speed_after=-0.2) == "Station rétrograde"
    assert _station_label(speed_before=-0.2, speed_after=0.5) == "Station directe"
    assert _station_label(speed_before=0.5, speed_after=0.3) is None
    assert _station_label(speed_before=-0.5, speed_after=-0.3) is None


# ---------------------------------------------------------------------------
# Logique pure : franchissements héliaques, table de vérité matin/soir x lever/coucher
# ---------------------------------------------------------------------------


def test_heliacal_label_truth_table():
    # Écart croissant (émerge de sous les rayons) -> "Lever".
    assert _heliacal_label(gap_before=10.0, gap_after=20.0, west_of_sun_after=True) == "Lever héliaque du matin"
    assert _heliacal_label(gap_before=10.0, gap_after=20.0, west_of_sun_after=False) == "Lever héliaque du soir"
    # Écart décroissant (disparaît sous les rayons) -> "Coucher".
    assert _heliacal_label(gap_before=20.0, gap_after=10.0, west_of_sun_after=True) == "Coucher héliaque du matin"
    assert _heliacal_label(gap_before=20.0, gap_after=10.0, west_of_sun_after=False) == "Coucher héliaque du soir"
    # Pas de franchissement du seuil : aucune étiquette.
    assert _heliacal_label(gap_before=20.0, gap_after=25.0, west_of_sun_after=True) is None
    assert _heliacal_label(gap_before=10.0, gap_after=12.0, west_of_sun_after=True) is None


def test_heliacal_label_boundary_is_inclusive_on_after_side():
    # gap_after exactement au seuil : compte comme franchi (<=).
    assert _heliacal_label(gap_before=14.0, gap_after=15.0, west_of_sun_after=True) == "Lever héliaque du matin"
    assert _heliacal_label(gap_before=15.0, gap_after=14.0, west_of_sun_after=True) == "Coucher héliaque du matin"


# ---------------------------------------------------------------------------
# Logique pure : détection sur série + sélection du plus proche
# ---------------------------------------------------------------------------


def test_find_crossings_detects_station_and_heliacal_on_synthetic_series():
    series = [
        _sample(-2, speed=1.0, gap_to_sun=10.0, west_of_sun=True),
        _sample(-1, speed=-0.5, gap_to_sun=16.0, west_of_sun=True),  # station rétrograde + lever héliaque du matin
        _sample(0, speed=-0.4, gap_to_sun=17.0, west_of_sun=True),
    ]
    crossings = _find_crossings(series)
    assert (-1, "Station rétrograde") in crossings
    assert (-1, "Lever héliaque du matin") in crossings
    assert len(crossings) == 2


def test_find_crossings_empty_when_no_change():
    series = [_sample(d, speed=1.0, gap_to_sun=90.0, west_of_sun=True) for d in range(-3, 4)]
    assert _find_crossings(series) == []


def test_nearest_event_picks_smallest_absolute_offset():
    series = [
        _sample(-10, speed=1.0, gap_to_sun=10.0, west_of_sun=True),
        _sample(-9, speed=-0.5, gap_to_sun=10.0, west_of_sun=True),  # station à J-9
        _sample(2, speed=-0.5, gap_to_sun=10.0, west_of_sun=True),
        _sample(3, speed=0.5, gap_to_sun=10.0, west_of_sun=True),  # station à J+3, plus proche de 0
    ]
    event = _nearest_event("Mars", series)
    assert event is not None
    assert event.days_from_birth == 3
    assert event.event_type == "Station directe"
    assert event.in_window is True


def test_nearest_event_none_when_no_crossing_in_series():
    series = [_sample(d, speed=1.0, gap_to_sun=90.0, west_of_sun=True) for d in range(-3, 4)]
    assert _nearest_event("Mars", series) is None


def test_nearest_event_out_of_window_when_beyond_seven_days():
    series = [
        _sample(9, speed=-0.5, gap_to_sun=90.0, west_of_sun=True),
        _sample(10, speed=0.5, gap_to_sun=90.0, west_of_sun=True),
    ]
    event = _nearest_event("Mars", series)
    assert event is not None
    assert event.days_from_birth == 10
    assert event.in_window is False


def test_nearest_event_tie_break_is_deterministic_first_encountered():
    # Un franchissement à J-3 et un autre à J+3 : distance absolue égale.
    # `_find_crossings` les ajoute dans l'ordre chronologique croissant, le
    # premier rencontré (J-3) doit donc l'emporter (départage documenté,
    # arbitraire mais déterministe).
    series = [
        _sample(-4, speed=1.0, gap_to_sun=90.0, west_of_sun=True),
        _sample(-3, speed=-0.5, gap_to_sun=90.0, west_of_sun=True),  # station à J-3
        _sample(2, speed=-0.5, gap_to_sun=90.0, west_of_sun=True),
        _sample(3, speed=0.5, gap_to_sun=90.0, west_of_sun=True),  # station à J+3
    ]
    event = _nearest_event("Mars", series)
    assert event is not None
    assert event.days_from_birth == -3


# ---------------------------------------------------------------------------
# Intégration réelle (Anthony, Liam) : plausibilité, aucune vérité terrain
# ---------------------------------------------------------------------------


def _real_phasis_events(fixture_name: str):
    fixture = load_fixture(fixture_name)
    birth = birth_data_from_fixture(fixture)
    observation = build_observation(birth)
    return observation.phasis


def test_anthony_phasis_events_are_plausible():
    events = _real_phasis_events("anthony")
    assert 0 < len(events) <= 5
    for event in events:
        assert event.event_type in _KNOWN_EVENT_TYPES
        assert -500 <= event.days_from_birth <= 500
        assert event.in_window == (abs(event.days_from_birth) <= PHASIS_WINDOW_DAYS)


def test_liam_phasis_events_are_plausible():
    events = _real_phasis_events("liam")
    assert 0 < len(events) <= 5
    for event in events:
        assert event.event_type in _KNOWN_EVENT_TYPES
        assert -500 <= event.days_from_birth <= 500
        assert event.in_window == (abs(event.days_from_birth) <= PHASIS_WINDOW_DAYS)


def test_compute_phasis_events_respects_custom_search_window():
    from hellenistic_astrology.core.timezone import resolve_utc

    fixture = load_fixture("anthony")
    birth = birth_data_from_fixture(fixture)
    utc_dt = resolve_utc(birth)
    jd_ut = ephemeris.julian_day_utc(utc_dt)
    ephemeris.set_ephemeris_path(DEFAULT_EPHE_PATH)
    flags = ephemeris.compute_flags(DEFAULT_EPHE_PATH)

    events = compute_phasis_events(jd_ut, flags, search_window_days=5)
    for event in events:
        assert -5 <= event.days_from_birth <= 5
