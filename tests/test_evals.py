"""Offline eval checks validate cases; they do not claim LLM behavior."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_offline_eval_suite_reports_cases_and_explicitly_not_model_execution():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evals.py")],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["passed"]
    assert data["case_count"] == 15
    assert data["positive_count"] == 10
    assert data["negative_count"] == 5
    assert data["model_evaluation_executed"] is False
