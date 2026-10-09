"""Safe question-file input reaches the real draw CLI, not a shell."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "draw.py"


def test_question_file_preserves_quotes_without_default_echo(tmp_path):
    question = "我该怎么处理 it's 这种情况？\n$(touch definitely-not-created)；生日：1990-05-15"
    path = tmp_path / "question.txt"
    path.write_text(question, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--question-file", str(path), "--seed", "42"],
        text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["question"] is None
    assert payload["question_provided"] is True
    assert payload["question_echoed"] is False
    assert "1990-05-15" not in result.stdout
    assert len(payload["cards"]) == 3
    assert not (tmp_path / "definitely-not-created").exists()


def test_oversized_question_file_is_rejected_cleanly(tmp_path):
    path = tmp_path / "too-large.txt"
    path.write_bytes(b"x" * (65536 + 1))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--question-file", str(path)],
        text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 2
    assert "65536" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout.strip()


def test_stdin_echo_requires_explicit_consent_and_does_not_weight_cards():
    question = "it's 中文\n不要执行 $(date)"
    base = [sys.executable, str(SCRIPT), "--seed", "91"]
    result = subprocess.run(base + ["--question-file", "-", "--echo-question"],
                            input=question, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["question"] == question
    assert payload["question_echoed"] is True
    comparison = subprocess.run(base, text=True, capture_output=True, timeout=10)
    assert payload["cards"] == json.loads(comparison.stdout)["cards"]


def test_direct_question_argument_is_not_echoed_by_default():
    result = subprocess.run([sys.executable, str(SCRIPT), "--question", "敏感姓名甲"],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0
    assert "敏感姓名甲" not in result.stdout
    assert json.loads(result.stdout)["question_provided"] is True


def test_question_sources_are_mutually_exclusive(tmp_path):
    path = tmp_path / "q.txt"
    path.write_text("q", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--question", "q", "--question-file", str(path)],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_missing_and_non_utf8_question_files_fail_cleanly(tmp_path):
    missing = tmp_path / "missing.txt"
    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff\xfe")
    for path in [missing, invalid]:
        result = subprocess.run([sys.executable, str(SCRIPT), "--question-file", str(path)],
                                text=True, capture_output=True, timeout=10)
        assert result.returncode == 2
        assert "Traceback" not in result.stderr
        assert not result.stdout.strip()
