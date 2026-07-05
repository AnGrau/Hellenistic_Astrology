import swisseph as swe

from hellenistic_astrology.core import ephemeris


def test_compute_flags_falls_back_to_moseph_without_ephe_files(tmp_path):
    flags = ephemeris.compute_flags(str(tmp_path))
    assert flags == (swe.FLG_MOSEPH | swe.FLG_SPEED)


def test_compute_flags_falls_back_to_moseph_when_directory_missing(tmp_path):
    missing = tmp_path / "does-not-exist"
    flags = ephemeris.compute_flags(str(missing))
    assert flags == (swe.FLG_MOSEPH | swe.FLG_SPEED)


def test_compute_flags_uses_swieph_when_ephe_files_present(tmp_path):
    (tmp_path / "sepl_18.se1").write_bytes(b"")
    flags = ephemeris.compute_flags(str(tmp_path))
    assert flags == (swe.FLG_SWIEPH | swe.FLG_SPEED)


def test_compute_flags_ignores_non_se1_files(tmp_path):
    (tmp_path / "readme.txt").write_text("not an ephemeris file")
    flags = ephemeris.compute_flags(str(tmp_path))
    assert flags == (swe.FLG_MOSEPH | swe.FLG_SPEED)
