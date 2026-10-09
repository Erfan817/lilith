"""Doctor must work without runtime packages and never install anything."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "lilith.py"


def test_doctor_checks_the_actual_interpreter_and_tarot_stays_stdlib():
    result = subprocess.run([sys.executable, "-S", str(CLI), "doctor", "--module", "tarot"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["module"] == "tarot"
    assert payload["python"]["executable"] == sys.executable
    assert payload["network_used"] is False
    assert payload["installed_anything"] is False
    assert payload["skill_name"] == "lilith-diviner"


def test_doctor_reports_missing_dependencies_without_site_packages():
    # The dispatcher intentionally starts a fresh Python process; -S must target doctor itself.
    result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts" / "doctor.py"), "--module", "bazi"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready"] is False
    assert any(not check["ready"] for check in payload["dependencies"])
    assert payload["installed_anything"] is False
    assert payload["repair_argv"][0][:4] == [sys.executable, "-m", "pip", "install"]
    assert "Traceback" not in result.stderr


def test_doctor_all_runtime_dependencies_are_ready_in_project_environment():
    result = subprocess.run([sys.executable, str(CLI), "doctor"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready"]
    assert {check["package"] for check in payload["dependencies"]} == {
        "lunar-python", "astronomy-engine", "tzdata"
    }
    assert payload["repair_argv"] == []
