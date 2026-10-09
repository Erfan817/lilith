"""Precision regressions: independent HKO almanac fixtures, not self-oracles."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bazi.py"


def run_bazi(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=20)


def chart(solar, hour=None, *args):
    command = ["--solar", solar, "--as-of", "2026-10-08", *args]
    if hour is not None:
        command += ["--hour", hour]
    result = run_bazi(*command)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def gz(data, name):
    pillar = data["pillars"][name]
    return pillar["gan"] + pillar["zhi"]


def test_lichun_2024_not_switched_by_the_old_seven_minute_error():
    # https://www.hko.gov.hk/tc/gts/astronomy/data/files/24SolarTerms_2024.xml
    # HKO Almanac 2024: Start of Spring, Feb 4 16:27 HKT (UTC+08).
    # The old approximation changes at 16:20:11, seven minutes too early.
    # Before Lichun: Gui-Mao year, Yi-Chou month; not Jia-Chen/Bing-Yin.
    data = chart("2024-02-04", "16:24")
    assert (gz(data, "year"), gz(data, "month")) == ("癸卯", "乙丑")


def test_full_yun_reports_unrounded_start_and_library_dayun_periods():
    data = chart("1990-05-15", "12:00", "--sex", "男")
    assert data["dayun"]["start_age"] == {"years": 7, "months": 3, "days": 3, "hours": 20}
    assert data["dayun"]["start_solar"] == "1997-08-19T08:00:00+08:00"
    assert data["engine"]["yun_sect"] == 2
    first = data["dayun"]["periods"][1]
    assert (first["ganzhi"], first["start_year"], first["end_year"],
            first["start_age"], first["end_age"]) == ("壬午", 1997, 2006, 8, 17)
    assert data["dayun"]["period_age_convention"] == "nominal-year-age"


def test_unknown_clock_has_bounded_correlated_candidates_not_noon_start():
    data = chart("2024-02-04", None, "--sex", "男")
    assert data["dayun"] is None
    assert gz(data, "hour") == "未知未知"
    assert gz(data, "year") == gz(data, "month") == "未知未知"
    assert data["uncertainty"]["pillars"]["year"] == ["癸卯", "甲辰"]
    assert data["uncertainty"]["pillars"]["month"] == ["乙丑", "丙寅"]
    assert data["uncertainty"]["pillars"]["day"] == ["戊戌", "己亥"]
    candidates = data["uncertainty"]["candidates"]
    assert 1 < len(candidates) <= 8
    assert {(c["pillars"]["year"], c["pillars"]["month"]) for c in candidates} == {
        ("癸卯", "乙丑"), ("甲辰", "丙寅")}
    assert all(c["pillars"]["hour"] is None for c in candidates)
    assert data["uncertainty"]["dayun"] == "clock-time-required"
    assert gz(data, "day") == "未知未知"


def test_unknown_clock_retains_stable_gan_and_no_invented_ten_god():
    data = chart("1990-05-15", None, "--sex", "男")
    assert gz(data, "year") == "庚午"
    assert gz(data, "month") == "辛巳"
    assert data["pillars"]["year"]["ten_god"] == "未知"
    assert data["dayun"] is None
    assert data["uncertainty"]["pillars"]["day"] == ["庚辰", "辛巳"]
    assert data["shensha"] == []


def test_iana_zone_changes_term_instant_but_day_hour_use_local_civil_time():
    before = chart("2024-02-04", "03:26", "--timezone", "America/New_York")
    after = chart("2024-02-04", "03:28", "--timezone", "America/New_York")
    assert (gz(before, "year"), gz(before, "month")) == ("癸卯", "乙丑")
    assert (gz(after, "year"), gz(after, "month")) == ("甲辰", "丙寅")
    assert gz(after, "day") == "戊戌"
    assert gz(after, "hour") == "甲寅"
    assert after["input"]["civil_time"] == "2024-02-04T03:28:00-05:00"
    assert after["input"]["calendar_time"] == "2024-02-04T16:28:00+08:00"
    assert after["conventions"]["timezone"] == "America/New_York"
    assert after["conventions"]["day_hour_basis"] == "local-civil"
    local_late = chart("2024-02-04", "22:59", "--timezone", "America/New_York")
    assert gz(local_late, "day") == "戊戌"  # Beijing is already Feb 5.


@pytest.mark.parametrize("solar,hour,zone,message", [
    ("2024-03-10", "02:30", "America/New_York", "不存在"),
    ("2024-11-03", "01:30", "America/New_York", "歧义"),
    ("1990-04-15", "02:30", "Asia/Shanghai", "不存在"),
    ("2024-02-04", "12:00", "Made/Up", "IANA"),
])
def test_iana_dst_gaps_ambiguities_and_invalid_zone_are_rejected(solar, hour, zone, message):
    result = run_bazi("--solar", solar, "--hour", hour, "--timezone", zone,
                      "--as-of", "2026-10-08")
    assert result.returncode == 2
    assert message in result.stderr
    assert "Traceback" not in result.stderr


def test_fold_selects_distinct_real_instants_and_preserves_local_day_hour():
    early = chart("2024-11-03", "01:30", "--timezone", "America/New_York", "--fold", "0")
    late = chart("2024-11-03", "01:30", "--timezone", "America/New_York", "--fold", "1")
    assert early["input"]["civil_time"].endswith("-04:00")
    assert late["input"]["civil_time"].endswith("-05:00")
    assert early["input"]["calendar_time"] == "2024-11-03T13:30:00+08:00"
    assert late["input"]["calendar_time"] == "2024-11-03T14:30:00+08:00"
    assert early["pillars"] == late["pillars"]


def test_default_beijing_does_not_silently_apply_historical_dst():
    data = chart("1990-04-15", "02:30")
    assert data["input"]["civil_time"] == "1990-04-15T02:30:00+08:00"
    assert data["conventions"]["day_hour_basis"] == "local-civil"


def test_unknown_clock_iana_candidates_use_local_day_and_actual_term_interval():
    data = chart("2024-02-04", None, "--timezone", "America/New_York", "--sex", "男")
    assert data["dayun"] is None
    candidates = data["uncertainty"]["candidates"]
    assert [c["interval"]["start"] for c in candidates] == [
        "2024-02-04T00:00:00-05:00", "2024-02-04T03:27:07-05:00", "2024-02-04T23:00:00-05:00"]
    assert [c["pillars"]["day"] for c in candidates] == ["戊戌", "戊戌", "己亥"]
    assert data["input"]["civil_time"] is None
    assert data["input"]["calendar_time"] is None


def test_shichen_uses_full_two_hour_domain_not_midpoint():
    data = chart("2024-02-04", None, "--shichen", "申", "--sex", "男")
    assert data["dayun"] is None
    assert gz(data, "day") == "戊戌"
    assert gz(data, "hour") == "庚申"
    candidates = data["uncertainty"]["candidates"]
    assert len(candidates) == 2
    assert candidates[0]["interval"] == {
        "start": "2024-02-04T15:00:00+08:00", "end_exclusive": "2024-02-04T16:27:07+08:00"}
    assert candidates[1]["interval"]["end_exclusive"] == "2024-02-04T17:00:00+08:00"


def test_unspecified_zi_preserves_early_late_day_and_hour_candidates():
    data = chart("2024-02-04", None, "--shichen", "子")
    assert data["dayun"] is None
    assert data["uncertainty"]["pillars"]["day"] == ["戊戌", "己亥"]
    assert data["uncertainty"]["pillars"]["hour"] == ["壬子", "甲子"]
    assert data["pillars"]["hour"]["gan"] == "未知"
    assert data["pillars"]["hour"]["zhi"] == "子"
    assert len(data["uncertainty"]["candidates"]) == 2


def test_unknown_clock_dst_has_no_imaginary_candidate_interval():
    data = chart("2024-03-10", None, "--timezone", "America/New_York")
    candidates = data["uncertainty"]["candidates"]
    assert len(candidates) <= 8
    assert any(c["interval"]["end_exclusive"] == "2024-03-10T03:00:00-04:00" for c in candidates)
    assert all("T02:" not in c["interval"]["start"] for c in candidates)


def test_unknown_time_on_a_skipped_iana_civil_date_is_rejected():
    result = run_bazi("--solar", "2011-12-30", "--timezone", "Pacific/Apia", "--as-of", "2026-10-08")
    assert result.returncode == 2
    assert "不存在" in result.stderr
    assert "Traceback" not in result.stderr


def test_true_solar_time_is_explicit_and_preserves_absolute_term_year_month():
    civil = chart("2024-02-04", "16:24")
    solar = chart("2024-02-04", "16:24", "--time-basis", "apparent-solar", "--longitude", "90")
    assert solar["conventions"]["true_solar_time"] is True
    assert solar["conventions"]["day_hour_basis"] == "local-apparent-solar"
    assert solar["conventions"]["term_basis"] == "absolute-instant"
    assert solar["input"]["pillar_time"] != solar["input"]["civil_time"]
    assert solar["input"]["calendar_time"] == civil["input"]["calendar_time"]
    assert (gz(solar, "year"), gz(solar, "month")) == (gz(civil, "year"), gz(civil, "month"))
    assert gz(solar, "hour") != gz(civil, "hour")
    correction = solar["conventions"]["solar_correction"]
    assert correction["longitude_degrees_east"] == 90
    assert correction["correction_minutes"] < -120


def test_apparent_solar_eot_matches_independent_noaa_fractional_formula():
    import math
    from datetime import datetime, timezone
    import importlib.util
    spec = importlib.util.spec_from_file_location("lilith_solar_time", ROOT / "scripts" / "bazi_engine.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "apparent_solar_clock"), "Missing real solar-time calculation"
    civil = datetime(2024, 2, 4, 16, 24, tzinfo=timezone(__import__("datetime").timedelta(hours=8)))
    clock, correction = module.apparent_solar_clock(civil, 120)
    utc = civil.astimezone(timezone.utc)
    gamma = 2 * math.pi / 366 * (utc.timetuple().tm_yday - 1 + (utc.hour - 12) / 24)
    independent = 229.18 * (.000075 + .001868 * math.cos(gamma) - .032077 * math.sin(gamma)
                            - .014615 * math.cos(2 * gamma) - .040849 * math.sin(2 * gamma))
    assert abs(correction["equation_of_time_minutes"] - independent) < .5
    assert -15 < correction["equation_of_time_minutes"] < -12
    assert clock.tzinfo is None  # A solar clock label is not a second physical instant.
    assert abs((clock - civil.replace(tzinfo=None)).total_seconds() / 60 - correction["correction_minutes"]) < .0001


@pytest.mark.parametrize("args", [
    ["--hour", "12:00", "--time-basis", "apparent-solar"],
    ["--time-basis", "apparent-solar", "--longitude", "120"],
    ["--shichen", "午", "--time-basis", "apparent-solar", "--longitude", "120"],
    ["--hour", "12:00", "--longitude", "120"],
    ["--hour", "12:00", "--time-basis", "apparent-solar", "--longitude", "nan"],
    ["--hour", "12:00", "--time-basis", "apparent-solar", "--longitude", "181"],
    ["--hour", "12:00", "--fold", "1"],
    ["--timezone", "Asia/Shanghai", "--fold", "0"],
])
def test_solar_and_fold_parameters_fail_cleanly_without_required_context(args):
    result = run_bazi("--solar", "1990-05-15", "--as-of", "2026-10-08", *args)
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_explicit_23_hour_day_boundary_uses_next_day_for_day_and_hour_stem():
    before = chart("2024-02-04", "22:59")
    after = chart("2024-02-04", "23:00")
    tomorrow = chart("2024-02-05", "00:00")
    assert gz(before, "day") == "戊戌"
    assert gz(after, "day") == gz(tomorrow, "day") == "己亥"
    assert gz(after, "hour") == gz(tomorrow, "hour") == "甲子"


@pytest.mark.parametrize("solar,zone,branch", [
    ("2100-12-31", "America/New_York", "酉"),
    ("2100-12-31", "America/New_York", None),
    ("1900-01-01", "Etc/GMT-14", "子"),
    ("1900-01-01", "Etc/GMT-14", None),
])
def test_unknown_clock_cannot_bypass_converted_calendar_range(solar, zone, branch):
    args = ["--solar", solar, "--timezone", zone, "--as-of", "2100-12-31"]
    if branch is not None:
        args += ["--shichen", branch]
    result = run_bazi(*args)
    assert result.returncode == 2, result.stderr
    assert "1900–2100" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_unknown_interval_exclusive_upper_endpoint_is_allowed_without_clipping():
    result = run_bazi("--solar", "2100-12-31", "--timezone", "America/New_York",
                      "--shichen", "巳", "--as-of", "2100-12-31")
    assert result.returncode == 0, result.stderr
    candidates = json.loads(result.stdout)["uncertainty"]["candidates"]
    assert candidates[-1]["interval"]["end_exclusive"] == "2100-12-31T11:00:00-05:00"


def test_unknown_beijing_last_day_still_accepts_full_half_open_day():
    result = run_bazi("--solar", "2100-12-31", "--as-of", "2100-12-31")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["dayun"] is None
    assert data["uncertainty"]["candidates"][-1]["interval"]["end_exclusive"] == "2101-01-01T00:00:00+08:00"
