"""Flow-year cutoffs must use real Lichun, not Gregorian year arithmetic."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def cutoff(value, birth_time_known=True, *extra):
    argv = [sys.executable, str(ROOT / "scripts/lilith.py"), "bazi", "--solar", "1990-05-15", "--as-of", value, *extra]
    if birth_time_known:
        argv += ["--hour", "12:00"]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("known", [True, False])
@pytest.mark.parametrize("day,expected", [("2024-01-15", "癸卯"), ("2024-02-03", "癸卯"), ("2024-02-05", "甲辰")])
def test_date_cutoff_uses_lichun_for_known_and_unknown_birth_times(known, day, expected):
    assert cutoff(day, known)["current_ganzhi"] == expected


@pytest.mark.parametrize("known", [True, False])
def test_lichun_date_without_cutoff_clock_keeps_both_year_candidates(known):
    data = cutoff("2024-02-04", known)
    assert data["current_ganzhi"] is None
    assert data["flow_year"]["ganzhi_candidates"] == ["癸卯", "甲辰"]
    assert data["flow_year"]["as_of_precision"] == "date"
    assert data["flow_year"]["boundary"] == "lichun"
    assert any("立春" in warning and "截止" in warning for warning in data["warnings"])


@pytest.mark.parametrize("instant,expected", [("2024-02-04T16:27:06+08:00", "癸卯"), ("2024-02-04T16:27:07+08:00", "甲辰"), ("2024-02-04T08:27:07Z", "甲辰")])
def test_explicit_cutoff_instant_changes_at_library_lichun_second(instant, expected):
    # A library second-resolution regression, not official almanac certification.
    data = cutoff(instant)
    assert data["current_ganzhi"] == expected
    assert data["flow_year"]["as_of_precision"] == "instant"


def test_year_only_deceased_cutoff_does_not_invent_death_date():
    data = cutoff("2026-10-08", True, "--deceased-year", "2024")
    assert data["current_year"] == 2024
    assert data["current_ganzhi"] is None
    assert data["flow_year"]["as_of_precision"] == "date"
    assert data["flow_year"]["deceased_precision"] == "year"
    assert data["flow_year"]["domain_precision"] == "year"
    assert data["flow_year"]["ganzhi_candidates"] == ["癸卯", "甲辰"]


def test_deceased_year_candidates_do_not_extend_past_analysis_cutoff():
    data = cutoff("2024-01-15", False, "--deceased-year", "2024")
    assert data["current_ganzhi"] == "癸卯"


def test_naive_cutoff_datetime_is_rejected_without_guessing_timezone():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/lilith.py"), "bazi", "--solar", "1990-05-15", "--as-of", "2024-02-04T16:28:00"], capture_output=True, text=True, timeout=20)
    assert result.returncode == 2
    assert not result.stdout
    assert "偏移" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("hour,zone,start", [
    ("17:00", None, "2024-02-04T17:00:00+08:00"),
    ("04:00", "America/New_York", "2024-02-04T17:00:00+08:00"),
])
def test_deceased_year_domain_starts_at_known_absolute_birth(hour, zone, start):
    args = [sys.executable, str(ROOT / "scripts/lilith.py"), "bazi", "--solar", "2024-02-04",
            "--hour", hour, "--as-of", "2024-12-31", "--deceased-year", "2024"]
    if zone:
        args += ["--timezone", zone]
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["current_ganzhi"] == "甲辰"
    assert data["flow_year"]["ganzhi_candidates"] == ["甲辰"]
    assert data["flow_year"]["interval"]["start"] == start


@pytest.mark.parametrize("hour,zone", [("17:00", None), ("04:00", "America/New_York")])
def test_instant_cutoff_before_actual_birth_is_rejected(hour, zone):
    args = [sys.executable, str(ROOT / "scripts/lilith.py"), "bazi", "--solar", "2024-02-04",
            "--hour", hour, "--as-of", "2024-02-04T16:27:06+08:00"]
    if zone:
        args += ["--timezone", zone]
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "出生" in result.stderr and "早于" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("hour,zone,cutoff_text", [
    ("17:00", None, "2024-02-04T17:00:00+08:00"),
    ("04:00", "America/New_York", "2024-02-04T09:00:00Z"),
])
def test_cutoff_equal_to_absolute_birth_is_accepted(hour, zone, cutoff_text):
    args = [sys.executable, str(ROOT / "scripts/lilith.py"), "bazi", "--solar", "2024-02-04",
            "--hour", hour, "--as-of", cutoff_text, "--deceased-year", "2024"]
    if zone:
        args += ["--timezone", zone]
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["current_ganzhi"] == "甲辰"
    assert data["flow_year"]["as_of_precision"] == "instant"
    assert data["flow_year"]["deceased_precision"] == "year"


def test_unknown_branch_uses_earliest_real_domain_not_midnight_for_death_year():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/lilith.py"), "bazi",
                             "--solar", "2024-02-04", "--shichen", "酉",
                             "--as-of", "2024-12-31", "--deceased-year", "2024"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["current_ganzhi"] == "甲辰"
    assert data["flow_year"]["interval"]["start"] == "2024-02-04T17:00:00+08:00"
    assert data["dayun"] is None


def test_date_cutoff_on_actual_birth_day_does_not_include_pre_birth_year():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/lilith.py"), "bazi",
                             "--solar", "2024-02-04", "--hour", "17:00", "--as-of", "2024-02-04"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["current_ganzhi"] == "甲辰"
    assert data["flow_year"]["interval"]["start"] == "2024-02-04T17:00:00+08:00"


def test_cutoff_compares_absolute_birth_not_local_calendar_date():
    # UTC+14 birth at local Feb 5 00:00 is Feb 4 18:00 Beijing.
    result = subprocess.run([sys.executable, str(ROOT / "scripts/lilith.py"), "bazi",
                             "--solar", "2024-02-05", "--hour", "00:00", "--timezone", "Etc/GMT-14",
                             "--as-of", "2024-02-04T19:00:00+08:00"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["current_ganzhi"] == "甲辰"
