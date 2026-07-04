import io
import json
from unittest.mock import patch

import pytest

from hellenistic_astrology.core.geocoding import GeocodingError, geocode, resolve_coordinates
from hellenistic_astrology.core.timezone import BirthData


class _FakeContextManager:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self._response

    def __exit__(self, *exc_info):
        return False


def _fake_response(payload):
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


def test_geocode_parses_first_result():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        result = geocode("Paris, France")

    assert result.latitude == 48.8566
    assert result.longitude == 2.3522
    assert result.display_name == "Paris, France"


def test_geocode_sends_user_agent():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        geocode("Paris, France")

    request = mock_urlopen.call_args[0][0]
    # urllib normalise la clé "User-Agent" en "User-agent" via Request.add_header.
    assert "hellenistic-astrology" in request.headers["User-agent"]


def test_geocode_raises_on_no_results():
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response([]))
        with pytest.raises(GeocodingError):
            geocode("Lieu inexistant xyz123")


def test_resolve_coordinates_prefers_explicit_lat_lon_without_network_call():
    birth = BirthData(name="Test", latitude=1.0, longitude=2.0, place="Ignoré")
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        result = resolve_coordinates(birth)

    assert result == (1.0, 2.0)
    mock_urlopen.assert_not_called()


def test_resolve_coordinates_geocodes_when_only_place_given():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        birth = BirthData(name="Test", place="Paris, France")
        result = resolve_coordinates(birth)

    assert result == (48.8566, 2.3522)


def test_resolve_coordinates_requires_lat_lon_or_place():
    birth = BirthData(name="Test")
    with pytest.raises(ValueError):
        resolve_coordinates(birth)
