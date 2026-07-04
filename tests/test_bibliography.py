import re
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from hellenistic_astrology.bibliography import REFERENCES, check_all


class _FakeContextManager:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self._response

    def __exit__(self, *exc_info):
        return False


def _fake_response(status: int):
    response = MagicMock()
    response.status = status
    return response


def test_references_match_claude_md():
    """Garde-fou anti-dérive : les URLs codées en dur ici doivent rester
    synchronisées avec la section bibliographique de CLAUDE.md."""
    claude_md = Path(__file__).resolve().parents[1] / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8")
    section = text.split("## Références bibliographiques de travail")[1].split("\n##")[0]
    urls_in_claude_md = set(re.findall(r"https?://\S+", section))
    assert {url for _, url in REFERENCES} == urls_in_claude_md


def test_check_all_reports_ok_when_every_url_succeeds():
    with patch("hellenistic_astrology.bibliography.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeContextManager(_fake_response(200))
        results = check_all()

    assert len(results) == len(REFERENCES)
    assert all(r.ok for r in results)


def test_check_all_falls_back_to_get_when_head_not_allowed():
    def side_effect(request, timeout):
        if request.get_method() == "HEAD":
            raise urllib.error.HTTPError(request.full_url, 405, "Method Not Allowed", None, None)
        return _FakeContextManager(_fake_response(200))

    with patch(
        "hellenistic_astrology.bibliography.urllib.request.urlopen", side_effect=side_effect
    ):
        results = check_all()

    assert all(r.ok for r in results)
    assert all("GET" in r.detail for r in results)


def test_check_all_reports_failure_on_network_error():
    with patch(
        "hellenistic_astrology.bibliography.urllib.request.urlopen",
        side_effect=urllib.error.URLError("pas de réseau"),
    ):
        results = check_all()

    assert all(not r.ok for r in results)
