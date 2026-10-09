"""Acceptance tests for the one public entry point."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lilith.py"


@pytest.mark.parametrize("system,args,field,value", [
    ("tarot", ["--spread", "single", "--seed", "42"], "spread", "single"),
    ("bazi", ["--solar", "1990-05-15", "--sex", "男"], "system", "bazi"),
    ("astrology", ["--datetime", "2000-01-01T12:00:00Z"], "zodiac", "tropical"),
])
def test_unified_cli_preserves_engine_output(system, args, field, value):
    assert SCRIPT.is_file(), "Missing unified entry point"
    result = subprocess.run([sys.executable, str(SCRIPT), system, *args], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[field] == value


def test_unimplemented_chart_engines_do_not_fabricate_output():
    assert SCRIPT.is_file(), "Missing unified entry point"
    for system in ("ziwei", "qimen"):
        result = subprocess.run([sys.executable, str(SCRIPT), system], capture_output=True, text=True, timeout=10)
        assert result.returncode == 2
        assert "盘面" in result.stderr
        assert not result.stdout.strip()


def test_unified_cli_writes_real_report(tmp_path):
    output = tmp_path / "tarot.html"
    result = subprocess.run([sys.executable, str(SCRIPT), "report", "--input",
                             str(ROOT / "examples" / "tarot-seeded.json"), "--output", str(output)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert "<svg" in output.read_text(encoding="utf-8")


def test_unified_cli_location_requires_permission_and_help_lists_new_tools():
    result = subprocess.run([sys.executable, str(SCRIPT), "location", "--query-file", "does-not-read.txt"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)["error_type"] == "network_permission_required"
    help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=10)
    assert all(name in help_result.stdout for name in ["doctor", "report", "location", "sources"])
