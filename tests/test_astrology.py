"""End-to-end astronomical data and chart calculation, no network."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "astrology.py"


def run_chart(*args):
    assert SCRIPT.is_file(), "Missing astrology CLI"
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=25)


def load_engine():
    assert SCRIPT.is_file(), "Missing astrology engine"
    spec = importlib.util.spec_from_file_location("mystic_astrology", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_j2000_positions_are_geocentric_tropical_and_ten_bodies():
    result = run_chart("--datetime", "2000-01-01T12:00:00+00:00")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["zodiac"] == "tropical"
    assert data["frame"] == "geocentric-apparent-ecliptic-of-date"
    assert len(data["bodies"]) == 10
    assert data["angles"] is None
    sun = data["bodies"]["Sun"]
    assert sun["longitude"] == pytest.approx(280.3687, abs=0.03)
    assert sun["sign"] == "摩羯座"
    assert data["bodies"]["Moon"]["longitude"] == pytest.approx(223.32, abs=0.1)
    assert sun["house"] is None
    assert all(0 <= b["longitude"] < 360 for b in data["bodies"].values())
    assert data["engine"]["name"] == "astronomy-engine"
    assert isinstance(data["aspects"], list)


def test_aspects_use_short_arc_and_explicit_orbs():
    mod = load_engine()
    result = mod.find_aspects({"a": {"longitude": 359}, "b": {"longitude": 1}, "c": {"longitude": 91}})
    ab = next(x for x in result if x["a"] == "a" and x["b"] == "b")
    assert ab["name"] == "合相"
    assert ab["separation"] == 2
    assert ab["orb"] == 2
    assert ab["allowed_orb"] == 8
    assert any(x["name"] == "刑相" for x in result)
    assert mod.find_aspects({"a": {"longitude": 0}, "b": {"longitude": 70}}) == []


def test_planet_motion_is_reported_and_wrap_safe():
    result = run_chart("--datetime", "2000-01-01T12:00:00Z")
    assert result.returncode == 0, result.stderr
    bodies = json.loads(result.stdout)["bodies"]
    assert bodies["Sun"]["longitude_speed_deg_per_day"] == pytest.approx(1.019, abs=0.03)
    assert bodies["Sun"]["motion"] == "direct"
    assert bodies["Moon"]["longitude_speed_deg_per_day"] > 10
    assert bodies["Saturn"]["motion"] == "retrograde"
    assert all(b["motion"] in {"direct", "retrograde", "near-stationary"} for b in bodies.values())


@pytest.mark.parametrize("latitude,longitude", [(0, 0), (39.9, 116.4), (-33.9, 151.2)])
def test_angles_are_eastern_horizon_and_upper_meridian(latitude, longitude):
    mod = load_engine()
    result = run_chart("--datetime", "2000-01-01T12:00:00Z", "--lat", str(latitude), "--lon", str(longitude))
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    import astronomy
    time = astronomy.Time.Parse("2000-01-01T12:00:00Z")
    observer = astronomy.Observer(latitude, longitude, 0)
    angles = data["angles"]
    asc_vec = astronomy.VectorFromSphere(astronomy.Spherical(0, angles["ASC"], 1), time)
    eq = astronomy.EquatorFromVector(astronomy.RotateVector(astronomy.Rotation_ECT_EQD(time), asc_vec))
    horizon = astronomy.Horizon(time, observer, eq.ra, eq.dec, astronomy.Refraction.Airless)
    assert abs(horizon.altitude) < 1e-6
    assert 0 < horizon.azimuth < 180
    mc_vec = astronomy.VectorFromSphere(astronomy.Spherical(0, angles["MC"], 1), time)
    mc_eq = astronomy.EquatorFromVector(astronomy.RotateVector(astronomy.Rotation_ECT_EQD(time), mc_vec))
    lst = (astronomy.SiderealTime(time) + longitude / 15) % 24
    assert abs((mc_eq.ra - lst + 12) % 24 - 12) < 1e-7
    assert (angles["ASC"] - angles["DSC"]) % 360 == pytest.approx(180)
    assert (angles["MC"] - angles["IC"]) % 360 == pytest.approx(180)
    assert len(data["houses"]["cusps"]) == 12
    assert data["houses"]["system"] == "whole-sign"
    assert all(1 <= b["house"] <= 12 for b in data["bodies"].values())


def test_equal_house_cusps_start_at_ascendant():
    result = run_chart("--datetime", "2000-01-01T12:00:00Z", "--lat", "39.9", "--lon", "116.4", "--houses", "equal")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["houses"]["cusps"][0] == pytest.approx(data["angles"]["ASC"])
    assert data["houses"]["cusps"][1] == pytest.approx((data["angles"]["ASC"] + 30) % 360)


@pytest.mark.parametrize("args", [
    ("--lat", "0"), ("--lon", "0"), ("--lat", "nan", "--lon", "0"),
    ("--lat", "90", "--lon", "0"), ("--lat", "30", "--lon", "181"),
])
def test_invalid_or_partial_location_is_rejected(args):
    result = run_chart("--datetime", "2000-01-01T12:00:00Z", *args)
    assert result.returncode == 2


def test_iana_timezone_equals_explicit_offset():
    offset = run_chart("--datetime", "2000-01-01T20:00:00+08:00")
    zone = run_chart("--datetime", "2000-01-01T20:00:00", "--timezone", "Asia/Shanghai")
    assert offset.returncode == zone.returncode == 0, zone.stderr
    assert json.loads(offset.stdout)["bodies"] == json.loads(zone.stdout)["bodies"]


@pytest.mark.parametrize("text", ["2000-01-01", "2000-01-01T12:00:00", "1800-01-01T12:00:00Z", "2000-13-01T12:00:00Z"])
def test_incomplete_out_of_range_or_invalid_time_rejected(text):
    result = run_chart("--datetime", text)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_dst_gap_is_rejected():
    result = run_chart("--datetime", "2024-03-10T02:30:00", "--timezone", "America/New_York")
    assert result.returncode == 2
    assert "不存在" in result.stderr


def test_dst_fold_requires_explicit_choice():
    args = ("--datetime", "2024-11-03T01:30:00", "--timezone", "America/New_York")
    ambiguous = run_chart(*args)
    assert ambiguous.returncode == 2
    assert "fold" in ambiguous.stderr
    earlier, later = run_chart(*args, "--fold", "0"), run_chart(*args, "--fold", "1")
    assert earlier.returncode == later.returncode == 0, earlier.stderr + later.stderr
    assert json.loads(earlier.stdout)["datetime_utc"].startswith("2024-11-03T05:30")
    assert json.loads(later.stdout)["datetime_utc"].startswith("2024-11-03T06:30")


@pytest.mark.parametrize("local,offset,zone,expected", [
    ("2101-01-01T00:30:00", "+14:00", "Pacific/Kiritimati",
     "2100-12-31T10:30:00+00:00"),
    ("1899-12-31T12:00:00", "-12:00", "Etc/GMT+12",
     "1900-01-01T00:00:00+00:00"),
    ("1900-01-01T00:00:00", "Z", "Etc/UTC", "1900-01-01T00:00:00+00:00"),
    ("2100-12-31T23:59:59.999999", "Z", "Etc/UTC",
     "2100-12-31T23:59:59.999999+00:00"),
])
def test_utc_range_accepts_equivalent_offset_and_iana_instants(local, offset, zone, expected):
    mod = load_engine()
    instant = datetime.fromisoformat(expected)
    assert mod.parse_datetime(local + offset) == instant
    assert mod.parse_datetime(local, zone) == instant


@pytest.mark.parametrize("local,offset,zone", [
    ("1900-01-01T00:00:00", "+14:00", "Etc/GMT-14"),
    ("1899-12-31T23:59:59.999999", "Z", "Etc/UTC"),
    ("2100-12-31T23:59:59", "-12:00", "Etc/GMT+12"),
    ("2101-01-01T00:00:00", "Z", "Etc/UTC"),
])
def test_utc_range_rejects_equivalent_offset_and_iana_instants(local, offset, zone):
    mod = load_engine()
    with pytest.raises(ValueError, match="UTC"):
        mod.parse_datetime(local + offset)
    with pytest.raises(ValueError, match="UTC"):
        mod.parse_datetime(local, zone)


@pytest.mark.parametrize("local,offset,zone,expected", [
    ("2101-01-01T00:30:00", "+14:00", "Pacific/Kiritimati",
     "2100-12-31T10:30:00+00:00"),
    ("1899-12-31T12:00:00", "-12:00", "Etc/GMT+12",
     "1900-01-01T00:00:00+00:00"),
])
def test_cross_year_cli_offset_and_iana_charts_are_identical(local, offset, zone, expected):
    explicit = run_chart("--datetime", local + offset)
    zoned = run_chart("--datetime", local, "--timezone", zone)
    assert explicit.returncode == zoned.returncode == 0, explicit.stderr + zoned.stderr
    a, b = json.loads(explicit.stdout), json.loads(zoned.stdout)
    assert a["datetime_utc"] == b["datetime_utc"] == expected
    assert a["bodies"] == b["bodies"]


@pytest.mark.parametrize("args", [
    ("--datetime", "1900-01-01T00:00:00+14:00"),
    ("--datetime", "1900-01-01T00:00:00", "--timezone", "Etc/GMT-14"),
    ("--datetime", "2100-12-31T23:59:59-12:00"),
    ("--datetime", "2100-12-31T23:59:59", "--timezone", "Etc/GMT+12"),
    ("--datetime", "2101-01-01T00:00:00Z"),
])
def test_utc_out_of_range_cli_is_rejected_cleanly(args):
    result = run_chart(*args)
    assert result.returncode == 2, result.stderr
    assert "UTC [1900-01-01T00:00:00Z, 2101-01-01T00:00:00Z)" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


@pytest.mark.parametrize("args", [
    ("--datetime", "2000-01-01T12:00:00", "--timezone", "No/Such_Zone"),
    ("--datetime", "2000-01-01T12:00:00", "--timezone", ""),
    ("--datetime", "2000-01-01T12:00:00", "--timezone", "/etc/UTC"),
    ("--datetime", "2000-01-01", "--timezone", "Asia/Shanghai"),
    ("--datetime", "2000-01-01T12:00:00Z", "--timezone", "Asia/Shanghai"),
    ("--datetime", "2000-01-01T12:00:00Z", "--fold", "0"),
])
def test_timezone_or_unconfirmed_time_errors_do_not_regress(args):
    result = run_chart(*args)
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()
