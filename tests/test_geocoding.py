import io
import json
import urllib.parse
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


def _query_params(mock_urlopen):
    request = mock_urlopen.call_args[0][0]
    return urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)


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


def test_geocode_does_not_flag_nearby_duplicates_as_ambiguous():
    # Nominatim renvoie parfois plusieurs entités OSM distinctes (ville et
    # département, par ex.) pour un même lieu réel, à quelques km d'écart.
    payload = [
        {"lat": "48.8588897", "lon": "2.3200410", "display_name": "Paris, France (a)"},
        {"lat": "48.8534951", "lon": "2.3483915", "display_name": "Paris, France (b)"},
        {"lat": "48.8588897", "lon": "2.3200410", "display_name": "Paris, France (a)"},
    ]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        result = geocode("Paris, France")

    assert result.latitude == 48.8588897
    assert result.longitude == 2.3200410


def test_geocode_raises_on_ambiguous_multiple_results():
    payload = [
        {"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"},
        {"lat": "33.6609", "lon": "-95.5555", "display_name": "Paris, Texas, États-Unis"},
    ]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        with pytest.raises(GeocodingError) as excinfo:
            geocode("Paris")

    assert "Paris, France" in str(excinfo.value)
    assert "Paris, Texas" in str(excinfo.value)


def test_geocode_requests_multiple_candidates_to_detect_ambiguity():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        geocode("Paris, France")

    assert _query_params(mock_urlopen)["limit"] == ["5"]


def test_geocode_passes_country_code_to_narrow_search():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        geocode("Paris", country_code="fr")

    assert _query_params(mock_urlopen)["countrycodes"] == ["fr"]


def test_geocode_omits_country_code_when_not_given():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        geocode("Paris, France")

    assert "countrycodes" not in _query_params(mock_urlopen)


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


def test_resolve_coordinates_passes_country_code_through():
    payload = [{"lat": "48.8566", "lon": "2.3522", "display_name": "Paris, France"}]
    with patch("hellenistic_astrology.core.geocoding.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(payload))
        birth = BirthData(name="Test", place="Paris", country_code="fr")
        resolve_coordinates(birth)

    assert _query_params(mock_urlopen)["countrycodes"] == ["fr"]
