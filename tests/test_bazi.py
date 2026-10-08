"""Wrapper acceptance tests separate from the unchanged calendar engine."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bazi.py"


def run_bazi(*args):
    assert SCRIPT.is_file(), "Missing unified BaZi CLI"
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=20)


def test_bazi_golden_chart_json_and_explicit_conventions():
    result = run_bazi("--solar", "1990-05-15", "--hour", "12:00", "--sex", "男", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert {name: p["gan"] + p["zhi"] for name, p in data["pillars"].items()} == {"year": "庚午", "month": "辛巳", "day": "庚辰", "hour": "壬午"}
    assert data["dayun"]["direction"] == "forward"
    assert data["conventions"]["timezone"] == "UTC+08:00"
    assert data["conventions"]["true_solar_time"] is False
    assert data["current_year"] == 2026
    assert data["warnings"]


@pytest.mark.parametrize("args", [
    ("--solar", "1800-01-01"), ("--solar", "2200-01-01"),
    ("--solar", "1990-05-15", "--lunar", "1990-04-22"),
    ("--solar", "1990-05-15", "--hour", "25:00"),
    ("--solar", "1990-05-15", "--as-of", "1989-01-01"),
])
def test_invalid_bazi_inputs_rejected_cleanly(args):
    result = run_bazi(*args, "--sex", "男")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_unknown_hour_stays_unknown_and_has_precision_warning():
    result = run_bazi("--solar", "1990-05-15", "--sex", "男", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["pillars"]["hour"]["gan"] == data["pillars"]["hour"]["zhi"] == "未知"
    assert any("未知出生时间" in warning for warning in data["warnings"])
    assert any("简式近似" in warning for warning in data["warnings"])


def test_lunar_input_matches_solar_input():
    a = run_bazi("--solar", "1990-05-15", "--hour", "12:00", "--sex", "男")
    b = run_bazi("--lunar", "1990-04-21", "--hour", "12:00", "--sex", "男")
    assert a.returncode == b.returncode == 0, a.stderr + b.stderr
    assert json.loads(a.stdout)["pillars"] == json.loads(b.stdout)["pillars"]


def test_lunar_day_thirty_is_not_rejected_as_gregorian_february():
    result = run_bazi("--lunar", "2023-02-30", "--sex", "男", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["input"]["solar"].startswith("2023-03-21")


def test_gender_convention_can_be_omitted_without_inventing_dayun():
    result = run_bazi("--solar", "1990-05-15", "--hour", "12:00", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["input"]["sex_convention"] is None
    assert data["dayun"] is None
    assert data["pillars"]["day"]["gan"] == "庚"
    assert any("顺逆参数" in warning for warning in data["warnings"])
    assert not any("元辰" in entry for entry in data["shensha"])


@pytest.mark.parametrize("deceased_year", [-1, 1899, 2101, 100000000])
def test_deceased_year_is_bounded_before_calendar_compute(deceased_year):
    # Keep the unfixed allocation regression safe: only the CLI child is limited.
    pytest.importorskip("resource")
    runner = (
        "import resource, runpy, sys; "
        "resource.setrlimit(resource.RLIMIT_AS, (128 * 1024**2, 128 * 1024**2)); "
        "sys.argv = sys.argv[1:]; "
        "runpy.run_path(sys.argv[0], run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-c", runner, str(SCRIPT), "--solar", "1990-05-15",
         "--deceased-year", str(deceased_year), "--as-of", "2026-10-08"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 2, result.stderr
    assert "1900–2100" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


@pytest.mark.parametrize("deceased_year", [1900, 1989])
def test_deceased_year_cannot_precede_solar_birth_year(deceased_year):
    result = run_bazi("--solar", "1990-05-15", "--deceased-year", str(deceased_year),
                      "--as-of", "2026-10-08")
    assert result.returncode == 2, result.stderr
    assert "逝世年份不能早于出生年份" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


@pytest.mark.parametrize("as_of", ["1899-12-31", "2101-01-01", "9999-12-31"])
def test_analysis_date_year_is_bounded(as_of):
    result = run_bazi("--solar", "1990-05-15", "--as-of", as_of)
    assert result.returncode == 2, result.stderr
    assert "分析年份需 1900–2100" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


@pytest.mark.parametrize("as_of,current_year", [
    ("1900-01-01", 1900), ("2100-12-31", 2100),
])
def test_analysis_date_inclusive_bounds_remain_valid(as_of, current_year):
    result = run_bazi("--solar", "1900-01-01", "--as-of", as_of)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["current_year"] == current_year


@pytest.mark.parametrize("deceased_year,as_of", [
    (2027, "2026-12-31"), (2030, "2026-10-08"), (2100, None),
])
def test_deceased_year_cannot_exceed_analysis_year(deceased_year, as_of):
    args = ["--solar", "1990-05-15", "--deceased-year", str(deceased_year)]
    if as_of is None:
        from datetime import datetime, timedelta, timezone
        if datetime.now(timezone(timedelta(hours=8))).year >= deceased_year:
            pytest.skip("No supported future death year remains for the live-date test")
    else:
        args += ["--as-of", as_of]
    result = run_bazi(*args)
    assert result.returncode == 2, result.stderr
    assert "逝世年份不能超过分析年份" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


@pytest.mark.parametrize("deceased_year,as_of,current_year", [
    (1990, "1990-05-15", 1990), (2010, "2026-10-08", 2010),
    (2026, "2026-10-08", 2026), (2100, "2100-12-31", 2100),
])
def test_valid_deceased_year_sets_consistent_cutoff(deceased_year, as_of, current_year):
    result = run_bazi("--solar", "1990-05-15", "--deceased-year", str(deceased_year),
                      "--as-of", as_of)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["current_year"] == current_year
    assert data["current_ganzhi"] == {
        1990: "庚午", 2010: "庚寅", 2026: "丙午", 2100: "庚申",
    }[current_year]


def test_default_analysis_date_cannot_precede_birth():
    from datetime import datetime, timedelta, timezone
    birth = "2100-12-31"
    if datetime.now(timezone(timedelta(hours=8))).date().isoformat() >= birth:
        pytest.skip("No supported future birth date remains for the live-date test")
    result = run_bazi("--solar", birth)
    assert result.returncode == 2, result.stderr
    assert "分析日期不能早于出生日期" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_bazi_production_lunar_dependency_is_pinned():
    assert "lunar-python==1.4.8" in (ROOT / "requirements.txt").read_text().splitlines()


@pytest.mark.parametrize("lunar,leap,solar,lunar_display", [
    ("2020-04-01", False, "2020-04-23", "2020年四月初一"),
    ("2020-04-01", True, "2020-05-23", "2020年闰四月初一"),
    ("2020-05-15", False, "2020-07-05", "2020年五月十五"),
    ("2025-06-01", True, "2025-07-25", "2025年闰六月初一"),
])
def test_lunar_conversion_matches_civil_calendar(lunar, leap, solar, lunar_display):
    args = ["--lunar", lunar, "--hour", "12:00", "--sex", "男", "--as-of", "2026-10-08"]
    if leap:
        args += ["--leap"]
    result = run_bazi(*args)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["input"]["solar"] == solar + " 12:00"
    assert data["input"]["lunar"] == lunar_display
    solar_result = run_bazi("--solar", solar, "--hour", "12:00", "--sex", "男",
                            "--as-of", "2026-10-08")
    assert solar_result.returncode == 0, solar_result.stderr
    assert data["pillars"] == json.loads(solar_result.stdout)["pillars"]


@pytest.mark.parametrize("solar,lunar_display", [
    ("2020-04-23", "2020年四月初一"),
    ("2020-05-23", "2020年闰四月初一"),
    ("2020-07-05", "2020年五月十五"),
    ("2025-07-25", "2025年闰六月初一"),
])
def test_solar_input_displays_correct_civil_lunar_date(solar, lunar_display):
    result = run_bazi("--solar", solar, "--hour", "23:30", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["input"]["lunar"] == lunar_display


@pytest.mark.parametrize("lunar,leap", [
    ("2020-04-30", True),  # Leap April has 29 days.
    ("2020-01-30", False),  # Ordinary January also has 29 days.
    ("2020-05-01", True),  # The old engine fabricated leap May.
    ("2025-07-01", True),  # Leap month is June, not July.
    ("2024-02-01", True),  # No leap month in 2024.
    ("2020-00-01", False), ("2020-13-01", False),
    ("2020-04-00", False), ("2020-04-31", False),
    ("2020-04", False), ("date-unknown", False),
])
def test_invalid_lunar_dates_and_nonexistent_leap_months_rejected_cleanly(lunar, leap):
    args = ["--lunar", lunar, "--as-of", "2026-10-08"]
    if leap:
        args += ["--leap"]
    result = run_bazi(*args)
    assert result.returncode == 2, result.stderr
    assert "农历" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_missing_production_calendar_dependency_is_reported_cleanly():
    # -S isolates the CLI from installed site-packages without mocking imports.
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "--solar", "1990-05-15"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 2, result.stderr
    assert "requirements.txt" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_precision_warning_distinguishes_civil_calendar_from_approximate_terms():
    result = run_bazi("--solar", "2020-05-23", "--as-of", "2026-10-08")
    assert result.returncode == 0, result.stderr
    warnings = json.loads(result.stdout)["warnings"]
    assert any("lunar-python" in warning and "节气" in warning and "简式近似" in warning
               for warning in warnings)
    assert not any("朔日" in warning or "特殊闰月" in warning for warning in warnings)


@pytest.mark.parametrize("solar,lunar,leap", [
    ("2020-04-23", "2020-04-01", False),
    ("2020-05-23", "2020-04-01", True),
    ("2020-07-05", "2020-05-15", False),
    ("2025-07-25", "2025-06-01", True),
])
def test_dual_solar_lunar_inputs_are_checked_with_civil_calendar(solar, lunar, leap):
    args = ["--lunar", lunar, "--as-of", "2026-10-08"]
    if leap:
        args += ["--leap"]
    matching = run_bazi("--solar", solar, *args)
    assert matching.returncode == 0, matching.stderr
    assert json.loads(matching.stdout)["input"]["solar"] == solar
    mismatching = run_bazi("--solar", "2020-06-06", *args)
    assert mismatching.returncode == 2, mismatching.stderr
    assert "公历与农历输入不一致" in mismatching.stderr
    assert "Traceback" not in mismatching.stderr
    assert not mismatching.stdout.strip()


def test_deceased_year_is_checked_against_converted_solar_birth_year():
    # Lunar 1990 December falls in solar 1991; the death year must not use 1990.
    result = run_bazi("--lunar", "1990-12-01", "--deceased-year", "1990",
                      "--as-of", "2026-10-08")
    assert result.returncode == 2, result.stderr
    assert "逝世年份不能早于出生年份" in result.stderr
    assert "Traceback" not in result.stderr
