"""Entry-point compatibility and narrow read/export permissions."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def front():
    return yaml.safe_load((ROOT / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])


def test_description_is_a_single_line_real_scalar_for_simple_parsers():
    lines = (ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()
    line = next(line for line in lines if line.startswith("description:"))
    plain = yaml.safe_load(line)["description"]
    assert plain == front()["description"]
    assert plain not in (">-", "|", "")
    assert "抽塔罗" in plain and "八字" in plain and "不用于" in plain


def test_sources_and_report_have_scoped_permissions_not_arbitrary_python():
    tools = front()["allowed-tools"]
    assert "Bash(python scripts/lilith.py sources *)" in tools
    assert "Bash(python scripts/lilith.py report *)" in tools
    assert "Bash(python *)" not in tools
    assert "location" not in tools  # Remote lookup keeps its own approval.
    entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "python scripts/lilith.py sources --module" in entry


def test_windows_acl_limit_is_visible_in_install_and_agent_instructions():
    for filename in ("SKILL.md", "README.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "Windows" in text and "ACL" in text, filename
