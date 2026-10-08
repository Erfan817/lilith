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
