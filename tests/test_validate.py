"""Repository validator contract; fixture is not a production knowledge base."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location("lilith_validate", ROOT / "scripts/validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_skill(tmp_path, frontmatter):
    root = tmp_path / "example-skill"
    root.mkdir()
    (root / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n# Instructions\n", encoding="utf-8")
    return root


def test_generic_audit_accepts_minimal_spec_and_long_description(tmp_path):
    description = "Extract structured evidence. Use when checking documents. " * 10
    root = write_skill(tmp_path, f"name: example-skill\ndescription: {description}")
    errors, stats = load_validator().audit(root)
    assert errors == []
    assert stats["skill_entries"] == 1


def test_validator_catches_missing_references_and_extra_skill(tmp_path):
    path = ROOT / "scripts" / "validate.py"
    assert path.is_file(), "Missing repository validator"
    spec = importlib.util.spec_from_file_location("mystic_validate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "SKILL.md").write_text("---\nname: lilith\ndescription: Use when exploring astrology.\nversion: 0.1.0\nauthor: Erfan\nlicense: MIT\nplatforms: [linux, macos, windows]\n---\n# Test\n[missing](references/missing.md)\n", encoding="utf-8")
    errors, stats = module.audit(tmp_path, project=True)
    assert any("missing.md" in error for error in errors)
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "SKILL.md").write_text("unwanted second skill", encoding="utf-8")
    errors, stats = module.audit(tmp_path, project=True)
    assert any("SKILL.md" in error and "1" in error for error in errors)


@pytest.mark.parametrize("name", ["Bad-name", "-bad", "bad-", "bad--name", "bad_name", "a" * 65, 7, "other-root"])
def test_generic_audit_rejects_invalid_or_mismatched_name(tmp_path, name):
    root = write_skill(tmp_path, f"name: {json.dumps(name)}\ndescription: Valid description")
    errors, _ = load_validator().audit(root)
    assert any("name" in error.lower() for error in errors)


@pytest.mark.parametrize("frontmatter, field", [
    ('name: example-skill\ndescription: ""', 'description'),
    ('name: example-skill\ndescription: "   "', 'description'),
    ('name: example-skill\ndescription: 2', 'description'),
    ('name: example-skill\ndescription: ' + 'x' * 1025, 'description'),
    ('name: example-skill\ndescription: Valid\ncompatibility: ' + 'x' * 501, 'compatibility'),
    ('name: example-skill\ndescription: Valid\ncompatibility: ""', 'compatibility'),
    ('name: example-skill\ndescription: Valid\nmetadata:\n  version: 2', 'metadata'),
    ('name: example-skill\ndescription: Valid\nmetadata: [bad]', 'metadata'),
    ('name: example-skill\ndescription: Valid\nlicense: [MIT]', 'license'),
    ('name: example-skill\ndescription: Valid\nallowed-tools: [Read]', 'allowed-tools'),
    ('name: example-skill\ndescription: Valid\nversion: "2"', 'version'),
    ('[not, a, mapping]', 'mapping'),
    ('name: [unclosed', 'frontmatter'),
])
def test_generic_audit_rejects_invalid_frontmatter_fields(tmp_path, frontmatter, field):
    root = write_skill(tmp_path, frontmatter)
    errors, _ = load_validator().audit(root)
    assert any(field in error.lower() for error in errors)


def test_generic_optional_fields_and_boundaries_are_portable(tmp_path):
    root = write_skill(tmp_path, '\n'.join([
        'name: example-skill', 'description: ' + 'x' * 1024,
        'compatibility: ' + 'x' * 500, 'license: MIT',
        'allowed-tools: Read Bash(git:*)', 'metadata:',
        '  arbitrary-key: arbitrary string', '  version: "2"',
    ]))
    (root / "assets").mkdir()
    (root / "assets" / "SKILL.md").write_text('Bundled example, not the install root', encoding='utf-8')
    errors, _ = load_validator().audit(root)
    assert errors == []


@pytest.mark.parametrize('description, expected', [
    ('Use when exploring tarot or astrology; not medical advice.', '中文'),
    ('这是一个帮助工具，用于反思，不用于医疗。', '触发'),
    ('塔罗八字紫微斗数奇门星座占星，不用于医疗。', '触发'),
    ('用户询问塔罗、八字、紫微、奇门或占星时使用。', '不用于'),
])
def test_project_description_checks_are_separate(description, expected):
    validator = load_validator()
    check = getattr(validator, 'validate_project_metadata', None)
    assert callable(check), 'Missing separate project metadata validator'
    errors = check({'name': 'lilith-diviner', 'description': description})
    assert any(expected in error for error in errors)


def test_project_description_accepts_chinese_triggers_and_boundary():
    validator = load_validator()
    check = getattr(validator, 'validate_project_metadata', None)
    assert callable(check), 'Missing separate project metadata validator'
    assert check({'name': 'lilith-diviner', 'description': '用户询问塔罗、八字、紫微、奇门或星座占星时使用；不用于医疗、投资或确定性预测。'}) == []


def test_validator_cli_exposes_generic_and_project_modes(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    generic = subprocess.run([sys.executable, str(ROOT / 'scripts/validate.py'), '--root', str(root), '--generic'],
                             text=True, capture_output=True)
    assert generic.returncode == 0, generic.stderr
    assert json.loads(generic.stdout)['passed'] is True
    project = subprocess.run([sys.executable, str(ROOT / 'scripts/validate.py'), '--root', str(root)],
                             text=True, capture_output=True)
    assert project.returncode == 1, project.stderr
    assert any('Project description' in error for error in json.loads(project.stdout)['errors'])


def test_stats_count_actual_additional_references_not_only_required_core(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    ref = root / 'references' / 'new-module' / 'extra.md'
    ref.parent.mkdir(parents=True)
    text = '# 新主题\n中文资料\n'
    ref.write_text(text, encoding='utf-8')
    errors, stats = load_validator().audit(root)
    assert errors == []
    assert stats['reference_files'] == 1
    assert stats['reference_characters'] == len(text)
    assert stats['required_core_reference_files'] == sum(len(names) for names in load_validator().MODULE_FILES.values())
    assert stats['modules']['new-module']['reference_files'] == 1


def stats_cli(root, *args):
    return subprocess.run([sys.executable, str(ROOT / 'scripts/update_stats.py'), '--root', str(root), *args],
                          text=True, capture_output=True)


def test_stats_cli_writes_deterministic_inventory_and_check_is_read_only(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    ref = root / 'references' / 'tarot' / 'new.md'
    ref.parent.mkdir(parents=True)
    ref.write_text('# 新主题\n中文资料\n', encoding='utf-8')
    historical = root / 'docs' / 'verification.json'
    historical.parent.mkdir()
    historical.write_text('{"historical": true}\n')
    first = stats_cli(root)
    assert first.returncode == 0, first.stderr
    target = root / 'docs' / 'stats.json'
    original = target.read_bytes()
    stats = json.loads(original)
    assert stats == load_validator().collect_stats(root)
    assert not any(key in stats for key in ('generated_at', 'timestamp'))
    second = stats_cli(root)
    assert second.returncode == 0, second.stderr
    assert target.read_bytes() == original
    checked = stats_cli(root, '--check')
    assert checked.returncode == 0, checked.stderr
    assert target.read_bytes() == original
    assert historical.read_text() == '{"historical": true}\n'


def test_stats_check_detects_stale_counts_without_rewriting(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    result = stats_cli(root)
    assert result.returncode == 0, result.stderr
    target = root / 'docs' / 'stats.json'
    original = target.read_bytes()
    added = root / 'references' / 'new-module' / 'added.md'
    added.parent.mkdir(parents=True)
    added.write_text('# Added reference\n')
    result = stats_cli(root, '--check')
    assert result.returncode == 1
    assert 'stale' in result.stderr.lower()
    assert target.read_bytes() == original
    assert stats_cli(root).returncode == 0
    assert json.loads(target.read_text())['reference_files'] == 1


def test_stats_check_missing_file_does_not_create_it(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    result = stats_cli(root, '--check')
    assert result.returncode == 1
    assert 'missing' in result.stderr.lower()
    assert not (root / 'docs' / 'stats.json').exists()


def test_stats_refuses_invalid_manifest_without_overwriting_existing_output(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    assert stats_cli(root).returncode == 0
    target = root / 'docs/stats.json'
    original = target.read_bytes()
    bad = root / 'references/tarot/sources.json'
    bad.parent.mkdir(parents=True)
    bad.write_text('{"sources": [{"url": "invalid"}]}')
    result = stats_cli(root)
    assert result.returncode == 1
    assert 'sources.json' in result.stderr and 'Traceback' not in result.stderr
    assert target.read_bytes() == original


def test_generic_mode_does_not_apply_tarot_or_astrology_coverage_rules(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for minimal document examples')
    signs = root / 'references/astrology/zodiac-signs.md'
    signs.parent.mkdir(parents=True)
    signs.write_text('# Generic fixture, not Lilith content\n')
    errors, _ = load_validator().audit(root)
    assert errors == []


def test_generic_description_no_chinese_is_valid_but_project_rejects_it(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for extracting documents; not medical advice.')
    assert load_validator().audit(root)[0] == []
    assert any('中文' in error for error in load_validator().audit(root, project=True)[0])


@pytest.mark.parametrize('directory', ['.venv', '.git', '.pytest_cache', '__pycache__'])
def test_stats_do_not_count_ignored_working_directories(tmp_path, directory):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    ignored = root / 'references' / directory / 'ignored.md'
    ignored.parent.mkdir(parents=True)
    ignored.write_text('# Runtime artifact\n')
    stats = load_validator().collect_stats(root)
    assert stats['reference_files'] == 0 and stats['markdown_files'] == 1


def test_install_root_ancestor_name_is_not_an_ignored_child_directory(tmp_path):
    ancestor = tmp_path / '.venv'
    ancestor.mkdir()
    root = write_skill(ancestor, 'name: example-skill\ndescription: Use for document extraction')
    reference = root / 'references' / 'extra.md'
    reference.parent.mkdir()
    reference.write_text('[missing](missing.md)\n')
    errors, stats = load_validator().audit(root)
    assert any('missing.md' in error for error in errors)
    assert stats['skill_entries'] == stats['reference_files'] == 1


def test_generic_skill_whitespace_body_is_rejected(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: Use for document extraction')
    (root / 'SKILL.md').write_text('---\nname: example-skill\ndescription: Use for documents\n---\n   \n')
    errors, _ = load_validator().audit(root)
    assert any('body' in error for error in errors)


def test_project_audit_never_executes_draw_script(tmp_path):
    root = write_skill(tmp_path, 'name: example-skill\ndescription: 用户问塔罗时使用，不用于医疗。')
    source = root / 'scripts' / 'draw.py'
    source.parent.mkdir()
    marker = tmp_path / 'untrusted-code-executed.txt'
    source.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("unexpected")\nDECK = []\n', encoding='utf-8')
    cards = root / 'references' / 'tarot' / 'cards.md'
    cards.parent.mkdir(parents=True)
    cards.write_text('# Synthetic incomplete cards\n', encoding='utf-8')
    errors, _ = load_validator().audit(root, project=True)
    assert not marker.exists(), 'Structure validation executed untrusted Python'
    assert any('Tarot' in error for error in errors)
