"""An unknown time is an interval, never silently a midnight natal chart."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "astrology.py"


def test_date_only_mode_reports_ranges_without_angles_or_exact_moon():
    result = subprocess.run([sys.executable, str(SCRIPT), "--date", "2000-01-01", "--timezone", "Asia/Shanghai"],
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["time_known"] is False
    assert payload["angles"] is None
    assert payload["houses"] is None
    assert payload["aspects"] is None
    assert payload["bodies"] is None
    assert payload["date_range"]["end_exclusive"] is True
    assert "Sun" in payload["body_ranges"]
    assert "Moon" in payload["body_ranges"]
    assert "sampled" in payload["range_method"]
    assert "longitude" not in payload["body_ranges"]["Moon"]


def test_date_only_mode_respects_dst_day_length():
    from datetime import datetime
    result = subprocess.run([sys.executable, str(SCRIPT), "--date", "2024-03-10", "--timezone", "America/New_York"],
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    span = json.loads(result.stdout)["date_range"]
    start, end = map(datetime.fromisoformat, [span["start_utc"], span["end_utc"]])
    assert (end - start).total_seconds() == 23 * 3600


def test_date_only_invalid_inputs_do_not_fabricate_natal_fields():
    for args in [
        ["--date", "2000-01-01"],
        ["--date", "2000-01-01", "--timezone", "Asia/Shanghai", "--lat", "39.9", "--lon", "116.4"],
        ["--date", "2000-02-30", "--timezone", "Asia/Shanghai"],
        ["--date", "2011-12-30", "--timezone", "Pacific/Apia"],
        ["--date", "2000-01-01", "--timezone", "Does/NotExist"],
        ["--date", "2101-01-01", "--timezone", "UTC"],
    ]:
        result = subprocess.run([sys.executable, str(SCRIPT), *args],
                                text=True, capture_output=True, timeout=20)
        assert result.returncode == 2, result.stderr
        assert "Traceback" not in result.stderr
        assert not result.stdout.strip()


def test_last_supported_utc_day_accepts_exclusive_upper_endpoint():
    result = subprocess.run([sys.executable, str(SCRIPT), "--date", "2100-12-31", "--timezone", "UTC"],
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["date_range"]["end_utc"] == "2101-01-01T00:00:00+00:00"
    assert payload["date_range"]["end_exclusive"] is True
