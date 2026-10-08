"""Repository validator contract; fixture is not a production knowledge base."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validator_catches_missing_references_and_extra_skill(tmp_path):
    path = ROOT / "scripts" / "validate.py"
    assert path.is_file(), "Missing repository validator"
    spec = importlib.util.spec_from_file_location("mystic_validate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "SKILL.md").write_text("---\nname: lilith\ndescription: Use when exploring astrology.\nversion: 0.1.0\nauthor: Erfan\nlicense: MIT\nplatforms: [linux, macos, windows]\n---\n# Test\n[missing](references/missing.md)\n", encoding="utf-8")
    errors, stats = module.audit(tmp_path)
    assert any("missing.md" in error for error in errors)
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "SKILL.md").write_text("unwanted second skill", encoding="utf-8")
    errors, stats = module.audit(tmp_path)
    assert any("SKILL.md" in error and "1" in error for error in errors)
