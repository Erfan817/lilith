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


def test_bazi_doctor_defaults_to_all_features_and_checks_solar_dependency():
    result = subprocess.run([sys.executable, str(CLI), "doctor", "--module", "bazi"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert {check["package"] for check in data["dependencies"]} == {
        "lunar-python", "tzdata", "astronomy-engine"
    }
    assert data["features"]["civil"]["ready"] is True
    assert data["features"]["apparent-solar"]["ready"] is True


def test_missing_solar_engine_fails_only_requested_solar_feature(monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location("doctor_feature_test", ROOT / "scripts/doctor.py")
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    real_find = doctor.importlib.util.find_spec
    monkeypatch.setattr(doctor.importlib.util, "find_spec", lambda name: None if name == "astronomy" else real_find(name))
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--module", "bazi", "--feature", "apparent-solar"])
    assert doctor.main() == 1
    solar = json.loads(capsys.readouterr().out)
    assert solar["ready"] is False
    assert solar["features"]["apparent-solar"]["ready"] is False
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--module", "bazi", "--feature", "civil"])
    assert doctor.main() == 0
    civil = json.loads(capsys.readouterr().out)
    assert civil["ready"] is True
    assert {item["package"] for item in civil["dependencies"]} == {"lunar-python", "tzdata"}


def test_feature_is_not_accepted_for_an_unrelated_module():
    result = subprocess.run([sys.executable, str(CLI), "doctor", "--module", "tarot", "--feature", "apparent-solar"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 2
    assert not result.stdout
    assert "bazi" in result.stderr
