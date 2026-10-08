"""Real CLI acceptance tests for the single skill's tarot engine."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "draw.py"


def run_draw(*args):
    assert SCRIPT.is_file(), "Missing uniform tarot draw CLI"
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=10)


@pytest.mark.parametrize("spread,count", [("single", 1), ("three", 3), ("diamond", 5), ("moon", 4), ("horseshoe", 7), ("celtic", 10)])
def test_seeded_spreads_are_unique_and_reproducible(spread, count):
    args = ("--spread", spread, "--seed", "42", "--question", "演示：复习习惯")
    first, second = run_draw(*args), run_draw(*args)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    a, b = json.loads(first.stdout), json.loads(second.stdout)
    assert a == b
    assert a["randomness"] == "seeded-pseudorandom"
    assert a["seed"] == 42
    assert a["algorithm"] == "uniform-without-replacement"
    assert len(a["cards"]) == count
    assert len({c["card"] for c in a["cards"]}) == count
    assert all(c["orientation"] in {"正位", "逆位"} for c in a["cards"])


def test_normal_draw_labels_secure_randomness():
    result = run_draw("--spread", "celtic")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["randomness"] == "system-random"
    assert data["seed"] is None
    assert data["reversed_probability"] == 0.5


@pytest.mark.parametrize("probability,orientation", [(0, "正位"), (1, "逆位")])
def test_orientation_probability_endpoints(probability, orientation):
    result = run_draw("--spread", "celtic", "--seed", "5", "--reversed-probability", str(probability))
    assert result.returncode == 0, result.stderr
    assert all(c["orientation"] == orientation for c in json.loads(result.stdout)["cards"])


@pytest.mark.parametrize("value", ["-0.1", "1.1", "nan", "inf"])
def test_invalid_reversal_probability_rejected(value):
    assert run_draw("--reversed-probability", value).returncode == 2


def test_full_deck_has_exactly_78_distinct_cards():
    import importlib.util
    spec = importlib.util.spec_from_file_location("draw", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert len(mod.DECK) == len(set(mod.DECK)) == 78
    assert mod.MAJORS[8] == "力量"
    assert mod.MAJORS[11] == "正义"
