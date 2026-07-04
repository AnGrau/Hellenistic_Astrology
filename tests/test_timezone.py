from datetime import date, datetime, time, timezone

import pytest

from hellenistic_astrology.core.timezone import BirthData, birth_data_from_dict, resolve_utc

PARIS_COORDS = {"latitude": 48.833056, "longitude": 2.326667}


def test_birth_data_from_dict_local_time_form():
    birth = birth_data_from_dict(
        {
            "name": "Anthony",
            "latitude": 48.833056,
            "longitude": 2.326667,
            "local_date": "1970-11-20",
            "local_time": "23:10:00",
            "tz_name": "Europe/Paris",
        }
    )
    assert birth == BirthData(
        name="Anthony",
        latitude=48.833056,
        longitude=2.326667,
        local_date=date(1970, 11, 20),
        local_time=time(23, 10),
        tz_name="Europe/Paris",
    )


def test_birth_data_from_dict_utc_form():
    birth = birth_data_from_dict(
        {
            "name": "Trop ancien",
            "latitude": 48.833056,
            "longitude": 2.326667,
            "utc_datetime": "1900-01-01T11:00:00+00:00",
        }
    )
    assert birth.utc_datetime == datetime(1900, 1, 1, 11, 0, tzinfo=timezone.utc)
    assert birth.local_date is None


def test_resolve_utc_winter_cet():
    # 20 novembre 1970, 23h10 CET (UTC+1, pas d'heure d'été en hiver) -> 22h10 UTC.
    birth = BirthData(
        name="Anthony",
        local_date=date(1970, 11, 20),
        local_time=time(23, 10),
        tz_name="Europe/Paris",
        **PARIS_COORDS,
    )
    assert resolve_utc(birth) == datetime(1970, 11, 20, 22, 10, tzinfo=timezone.utc)


def test_resolve_utc_summer_cest():
    # 19 octobre 2005, 15h50 CEST (UTC+2, heure d'été jusqu'au 30/10/2005) -> 13h50 UTC.
    birth = BirthData(
        name="Liam",
        local_date=date(2005, 10, 19),
        local_time=time(15, 50),
        tz_name="Europe/Paris",
        **PARIS_COORDS,
    )
    assert resolve_utc(birth) == datetime(2005, 10, 19, 13, 50, tzinfo=timezone.utc)


def test_resolve_utc_rejects_dates_before_1916():
    birth = BirthData(
        name="Trop ancien",
        local_date=date(1900, 1, 1),
        local_time=time(12, 0),
        tz_name="Europe/Paris",
        **PARIS_COORDS,
    )
    with pytest.raises(ValueError):
        resolve_utc(birth)


def test_resolve_utc_accepts_explicit_utc_before_1916():
    birth = BirthData(
        name="Trop ancien mais UTC fourni",
        utc_datetime=datetime(1900, 1, 1, 11, 0, tzinfo=timezone.utc),
        **PARIS_COORDS,
    )
    assert resolve_utc(birth) == datetime(1900, 1, 1, 11, 0, tzinfo=timezone.utc)
