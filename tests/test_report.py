"""Local report behavior and subprocess acceptance tests (synthetic fixtures only)."""
import copy
import errno
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report.py"
NS = {"s": "http://www.w3.org/2000/svg"}


def report_module():
    assert SCRIPT.is_file(), "Missing optional local report renderer"
    spec = importlib.util.spec_from_file_location("lilith_report_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def example(kind):
    name = {"tarot": "tarot-seeded", "astrology": "astrology-j2000", "bazi": "bazi-synthetic"}[kind]
    return json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))


def svg_tree(document):
    match = re.search(r"<svg\b.*?</svg>", document, re.DOTALL)
    assert match, "Report must contain a real inline SVG"
    return ET.fromstring(match.group())


def run_report(input_path, output_path, *flags):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output_path), *flags],
        capture_output=True, text=True, timeout=15,
    )


@pytest.fixture
def symlink_factory():
    def create(link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except NotImplementedError as error:
            pytest.skip(f"symlink creation is unavailable: {error}")
        except OSError as error:
            unsupported_errno = error.errno in (errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENOTSUP)
            unsupported_windows_error = getattr(error, "winerror", None) in (1, 50, 1314)
            if not (unsupported_errno or unsupported_windows_error):
                raise
            pytest.skip(f"symlink creation is unsupported or not permitted: {error}")
        if not link.is_symlink():
            pytest.skip("symlink creation returned without creating a symlink")
        return link

    return create


def test_three_card_report_draws_actual_cards_at_distinct_slots():
    payload = example("tarot")
    document = report_module().render_report(payload)
    svg = svg_tree(document)
    cards = svg.findall("s:g[@class='tarot-card']", NS)
    assert len(cards) == 3
    assert [node.attrib["data-card"] for node in cards] == [row["card"] for row in payload["cards"]]
    assert [node.attrib["data-orientation"] for node in cards] == [row["orientation"] for row in payload["cards"]]
    assert len({node.attrib["transform"] for node in cards}) == 3
    for node in cards:
        assert node.find("s:g", NS).attrib["transform"] == "rotate(180 56 85)"
        assert node.find("s:g/s:rect", NS) is not None
    assert "合成示例：复习习惯" not in document
    assert all(row["position"] in document and row["card"] in document for row in payload["cards"])
    assert "uniform-without-replacement" in document
    assert "<!doctype html>" in document.lower()
    assert "<script" not in document.lower()
    assert "http://www.w3.org/2000/svg" in document  # namespace, not a network resource


@pytest.mark.parametrize("change", [
    {"schema_version": "9.0"},
    {"system": "astrology"},
    {"spread": "celtic"},
    {"cards": []},
    {"cards": [{}]},
    {"bodies": {}},
    {"randomness": "unknown"},
    {"reversed_probability": float("inf")},
    {"reversed_probability": True},
])
def test_tarot_schema_mismatch_is_a_clean_validation_error(change):
    payload = example("tarot")
    payload.update(change)
    module = report_module()
    with pytest.raises(ValueError, match="报告输入"):
        module.render_report(payload)


def test_tarot_validator_returns_only_share_allowlisted_fields():
    payload = example("tarot")
    payload["notes"] = "SYNTHETIC_PRIVATE_NOTE"
    payload["revised"] = "SYNTHETIC_PRIVATE_REVISION"
    module = report_module()
    model = module.validate_payload(payload)
    assert model["kind"] == "tarot"
    assert model["cards"] == [
        {key: row[key] for key in ("position", "card", "orientation")} for row in payload["cards"]
    ]
    assert "question" not in model and "seed" not in model
    assert "SYNTHETIC_PRIVATE" not in json.dumps(model)
    assert module.render_report(payload) == module.render_report(example("tarot"))


@pytest.mark.parametrize("mutate", [
    lambda data: data["cards"][0].update(orientation="unknown"),
    lambda data: data["cards"][0].update(card='<script>alert(1)</script>'),
    lambda data: data["cards"][0].update(position="revised at secret address"),
    lambda data: data["cards"][0].update(is_major=False),
    lambda data: data["cards"][1].update(card=data["cards"][0]["card"]),
])
def test_tarot_rejects_noncanonical_or_inconsistent_card_records(mutate):
    payload = example("tarot")
    mutate(payload)
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


@pytest.mark.parametrize("spread,count", [("single", 1), ("three", 3), ("diamond", 5), ("moon", 4), ("horseshoe", 7), ("celtic", 10)])
def test_all_calculated_spreads_fit_their_declared_svg_layout(spread, count):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "draw.py"), "--spread", spread, "--seed", "42"],
        capture_output=True, text=True, check=True, timeout=10,
    )
    payload = json.loads(result.stdout)
    module = report_module()
    model = module.validate_payload(payload)
    svg = ET.fromstring(module.tarot_svg(model))
    groups = svg.findall("s:g[@class='tarot-card']", NS)
    assert len(groups) == count
    assert [g.attrib["data-card"] for g in groups] == [row["card"] for row in payload["cards"]]
    width, height = map(float, svg.attrib["viewBox"].split()[2:])
    transforms = []
    for group in groups:
        transform = group.attrib["transform"]
        x, y = map(float, re.fullmatch(r"translate\(([-\d.]+) ([-\d.]+)\)", transform).groups())
        assert 0 <= x and x + 112 <= width
        assert 16 <= y and y + 225 <= height
        transforms.append((x, y))
    assert len(set(transforms)) == count
    if spread == "diamond":
        assert transforms[0][1] > transforms[1][1]
        assert transforms[2][0] < transforms[0][0] < transforms[3][0]
    if spread == "celtic":
        assert all(x > transforms[0][0] for x, _ in transforms[6:])
        cross = groups[1].find("s:g", NS)
        assert "rotate(90 56 85)" in cross.attrib["transform"]


def test_upright_cards_are_not_flipped():
    payload = example("tarot")
    for card in payload["cards"]:
        card["orientation"] = "正位"
    svg = svg_tree(report_module().render_report(payload))
    assert all(node.attrib["transform"] == "rotate(0 56 85)" for node in svg.findall("s:g/s:g", NS))


def test_astrology_svg_uses_each_body_longitude_and_all_calculated_angles():
    payload = example("astrology")
    module = report_module()
    model = module.validate_payload(payload)
    assert model["kind"] == "astrology"
    assert module.validate_astrology(payload) == model
    svg = ET.fromstring(module.astrology_svg(model))
    markers = svg.findall("s:circle[@class='body-marker']", NS)
    assert len(markers) == 10
    for marker in markers:
        longitude = payload["bodies"][marker.attrib["data-body"]]["longitude"]
        assert float(marker.attrib["data-longitude"]) == pytest.approx(longitude)
        radius = float(marker.attrib["data-radius"])
        assert float(marker.attrib["cx"]) == pytest.approx(360 - radius * math.cos(math.radians(longitude)), abs=.001)
        assert float(marker.attrib["cy"]) == pytest.approx(360 + radius * math.sin(math.radians(longitude)), abs=.001)
    angles = svg.findall("s:line[@class='angle-marker']", NS)
    assert {node.attrib["data-angle"] for node in angles} == {"ASC", "DSC", "MC", "IC"}
    for line in angles:
        longitude = payload["angles"][line.attrib["data-angle"]]
        assert float(line.attrib["data-longitude"]) == pytest.approx(longitude)
        assert float(line.attrib["x2"]) == pytest.approx(360 - 250 * math.cos(math.radians(longitude)), abs=.001)
        assert float(line.attrib["y2"]) == pytest.approx(360 + 250 * math.sin(math.radians(longitude)), abs=.001)
    assert len(svg.findall("s:line[@class='house-cusp']", NS)) == 12
    assert len(svg.findall("s:text[@class='sign-label']", NS)) == 12
    document = module.render_report(payload)
    assert "摩羯座" in document and "第6宫" in document
    assert "whole-sign" in document and "astronomy-engine" in document
    assert payload["datetime_utc"] not in document
    assert "39.9" not in document and "116.4" not in document
    assert "aspects" not in document and "longitude_speed" not in document
    assert svg_tree(document).attrib["viewBox"] == "0 0 720 720"


def test_astrology_projection_discards_all_unapproved_fields():
    payload = example("astrology")
    payload.update(name="SYNTHETIC_NAME", notes="SYNTHETIC_NOTE", revised="SYNTHETIC_REVISION")
    for row in payload["bodies"].values():
        row["notes"] = "SYNTHETIC_BODY_NOTE"
    for row in payload["aspects"]:
        row["name"] = "SYNTHETIC_ASPECT_REVISION"
    model = report_module().validate_payload(payload)
    serialized = json.dumps(model)
    assert "SYNTHETIC" not in serialized
    assert all(key not in model for key in ("datetime_utc", "location", "input", "name", "notes", "aspects"))
    assert all("latitude" not in row and "motion" not in row for row in model["bodies"].values())


@pytest.mark.parametrize("mutate", [
    lambda data: data.update(schema_version="9.0"),
    lambda data: data.update(system="tarot"),
    lambda data: data.update(cards=[]),
    lambda data: data.update(zodiac="sidereal"),
    lambda data: data.update(frame="secret birthplace"),
    lambda data: data["engine"].update(name="unverified"),
    lambda data: data["engine"].update(version='1.0;url(https://evil.test)'),
    lambda data: data["bodies"].pop("Pluto"),
    lambda data: data["bodies"].update(Secret={}),
    lambda data: data["bodies"]["Sun"].update(longitude=float("nan")),
    lambda data: data["bodies"]["Sun"].update(longitude=float("inf")),
    lambda data: data["bodies"]["Sun"].update(longitude=360),
    lambda data: data["bodies"]["Sun"].update(longitude="280.0"),
    lambda data: data["bodies"]["Sun"].update(sign="双鱼座"),
    lambda data: data["bodies"]["Sun"].update(sign_degree=0),
    lambda data: data["bodies"]["Sun"].update(name="revised secret name"),
    lambda data: data["bodies"]["Sun"].update(house=3),
    lambda data: data["bodies"]["Sun"].update(house=True),
    lambda data: data["angles"].update(DSC=0),
    lambda data: data["angles"].pop("IC"),
    lambda data: data["houses"].update(system="placidus"),
    lambda data: data["houses"]["cusps"].pop(),
    lambda data: data["houses"]["cusps"].__setitem__(2, float("inf")),
    lambda data: data["houses"]["cusps"].__setitem__(1, 151),
    lambda data: data.update(angles=None),
])
def test_astrology_rejects_inconsistent_or_unsupported_result_contract(mutate):
    payload = example("astrology")
    mutate(payload)
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


def test_safe_warnings_map_known_messages_without_echoing_unknown_text():
    payload = example("astrology")
    payload["warnings"] += [
        "高纬度上升点变化特殊，仅支持整宫/等宫；勿按每两小时一星座推断。",
        "SYNTHETIC_SECRET at 2037-08-19 08:17 in <svg onload=alert(1)>secret-place</svg>",
    ]
    module = report_module()
    warnings = module.safe_warnings(payload, "astrology")
    assert any("高纬度" in warning for warning in warnings)
    assert any("隐藏" in warning and "核验" in warning for warning in warnings)
    document = module.render_report(payload)
    assert "Warnings / 注意事项" in document
    assert "SYNTHETIC_SECRET" not in document
    assert "2037-08-19" not in document
    assert "secret-place" not in document
    assert "onload=" not in document
    assert "天体位置" in document


@pytest.mark.parametrize("kind", ["tarot", "astrology"])
def test_private_mode_includes_true_original_fields_only_as_escaped_text(kind):
    payload = example(kind)
    attack = '</pre><script>alert("SYNTHETIC_SCRIPT")</script><img src="https://invalid.test/x" onerror="alert(1)"> &'
    payload["notes"] = attack
    payload["revised"] = {attack: "SYNTHETIC_REVISED_DATE 2037-08-19 08:17"}
    payload["name"] = "SYNTHETIC_NAME"
    payload["birth"] = "SYNTHETIC_BIRTH"
    payload["warnings"] = [attack]
    module = report_module()
    shared = module.render_report(payload)
    assert all(marker not in shared for marker in ("SYNTHETIC_NAME", "SYNTHETIC_BIRTH", "SYNTHETIC_SCRIPT", "SYNTHETIC_REVISED_DATE"))
    private = module.render_report(payload, private=True)
    assert "私密版" in private and "不可公开分享" in private
    assert "SYNTHETIC_NAME" in private and "SYNTHETIC_REVISED_DATE" in private
    assert "&lt;script&gt;" in private and "&lt;img" in private
    assert "<script" not in private and '<img src="https://' not in private
    from html import unescape
    original = re.search(r'<pre id="original-input">(.*?)</pre>', private, re.DOTALL)
    assert original is not None
    assert json.loads(unescape(original.group(1))) == payload
    assert "Content-Security-Policy" in private
    assert "script-src 'none'" in private and "connect-src 'none'" in private


def test_astrology_without_location_draws_only_calculated_bodies():
    payload = example("astrology")
    payload.update(angles=None, houses=None, location=None)
    for row in payload["bodies"].values():
        row["house"] = None
    payload["warnings"].append("未提供经纬度，未计算上升、天顶与宫位。")
    module = report_module()
    model = module.validate_payload(payload)
    assert model["angles"] is None and model["houses"] is None
    svg = svg_tree(module.render_report(payload))
    assert len(svg.findall("s:circle[@class='body-marker']", NS)) == 10
    assert not svg.findall("s:line[@class='angle-marker']", NS)
    assert not svg.findall("s:line[@class='house-cusp']", NS)
    assert "输入未计算角点与宫位" in module.render_report(payload)


def test_unknown_birth_time_day_range_is_explicitly_rejected_not_a_single_chart():
    payload = example("astrology")
    payload.update(mode="unknown-time-day-range", time_known=False,
                   date="SYNTHETIC_DATE", timezone="SYNTHETIC_TIMEZONE", body_ranges={},
                   bodies=None, angles=None, houses=None, aspects=None)
    module = report_module()
    for renderer in (module.validate_payload, module.validate_astrology, module.render_report):
        with pytest.raises(ValueError, match="未知生时.*范围.*不绘制单一星盘") as error:
            renderer(payload)
        assert "SYNTHETIC" not in str(error.value)
    # A conflicting mode/body record must not bypass the unknown-time gate.
    payload["bodies"] = example("astrology")["bodies"]
    with pytest.raises(ValueError, match="未知生时"):
        module.render_report(payload)


def test_bazi_is_identified_as_explicitly_unsupported_without_fabrication():
    with pytest.raises(ValueError, match="八字.*未支持"):
        report_module().render_report(example("bazi"))


@pytest.mark.parametrize("kind,count", [("tarot", 3), ("astrology", 10)])
def test_standalone_cli_exports_self_contained_report_without_saving_json(tmp_path, kind, count):
    output = tmp_path / "output.html"
    before = set(tmp_path.iterdir())
    result = run_report(ROOT / "examples" / {"tarot": "tarot-seeded.json", "astrology": "astrology-j2000.json"}[kind], output)
    assert result.returncode == 0, result.stderr
    assert output.is_file(), "Successful CLI must write the requested report"
    document = output.read_text(encoding="utf-8")
    svg = svg_tree(document)
    nodes = svg.findall("s:g[@class='tarot-card']", NS) if kind == "tarot" else svg.findall("s:circle[@class='body-marker']", NS)
    assert len(nodes) == count
    assert "分享版" in document
    assert set(tmp_path.iterdir()) - before == {output}
    assert "question" not in document and "datetime_utc" not in document
    assert "<script" not in document
    assert not re.search(r'<(?:img|link|script|image)\b', document, re.I)
    assert not re.search(r'\son\w+\s*=', document, re.I)
    assert "url(" not in document and "@import" not in document
    assert "JSON" not in result.stdout or "原始 JSON" not in result.stdout


def test_main_returns_zero_and_writes_the_requested_path(tmp_path):
    module = report_module()
    output = tmp_path / "report.html"
    assert module.main(["--input", str(ROOT / "examples" / "tarot-seeded.json"), "--output", str(output)]) == 0
    assert output.exists()


def test_cli_requires_output_path_instead_of_implicit_worktree_export(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(ROOT / "examples" / "tarot-seeded.json")],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "--output" in result.stderr
    assert not result.stdout.strip()


def test_cli_does_not_overwrite_without_explicit_flag(tmp_path):
    output = tmp_path / "report.html"
    output.write_text("EXISTING_SYNTHETIC_REPORT", encoding="utf-8")
    result = run_report(ROOT / "examples" / "tarot-seeded.json", output)
    assert result.returncode == 2
    assert "--overwrite" in result.stderr
    assert output.read_text(encoding="utf-8") == "EXISTING_SYNTHETIC_REPORT"
    result = run_report(ROOT / "examples" / "tarot-seeded.json", output, "--overwrite")
    assert result.returncode == 0, result.stderr
    assert "EXISTING_SYNTHETIC_REPORT" not in output.read_text(encoding="utf-8")


@pytest.mark.parametrize("kind", ["tarot", "astrology"])
def test_cli_private_escaping_and_default_share_redaction(tmp_path, kind):
    payload = example(kind)
    marker = 'SYNTHETIC_PERSONAL 2037-08-19 08:17 <script>alert("X")</script> &'
    payload.update(name=marker, notes=marker, revised={marker: marker}, question=marker,
                   input={"birthday": marker, "birthplace": marker}, datetime_utc=marker, location={"place": marker})
    payload["warnings"] = [marker]
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    shared_path, private_path = tmp_path / "share.html", tmp_path / "private.html"
    shared = run_report(input_path, shared_path)
    assert shared.returncode == 0, shared.stderr
    assert "SYNTHETIC_PERSONAL" not in shared_path.read_text(encoding="utf-8")
    private = run_report(input_path, private_path, "--private")
    assert private.returncode == 0, private.stderr
    text = private_path.read_text(encoding="utf-8")
    assert "SYNTHETIC_PERSONAL" in text and "&lt;script&gt;" in text
    assert "<script" not in text and "不可公开分享" in text
    assert "SYNTHETIC_PERSONAL" not in private.stdout + private.stderr
    assert "不可公开分享" in private.stderr


@pytest.mark.parametrize("kind", ["bazi", "unknown-time"])
def test_cli_unsupported_input_fails_with_exit_two_and_no_report(tmp_path, kind):
    input_path = ROOT / "examples" / "bazi-synthetic.json"
    if kind == "unknown-time":
        payload = example("astrology")
        payload.update(mode="unknown-time-day-range", time_known=False, date="SYNTHETIC_DATE", timezone="SYNTHETIC_TIMEZONE",
                       bodies=None, angles=None, houses=None, aspects=None, body_ranges={})
        input_path = tmp_path / "range.json"
        input_path.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "result.html"
    result = run_report(input_path, output)
    assert result.returncode == 2
    assert ("八字" if kind == "bazi" else "未知生时") in result.stderr
    assert "Traceback" not in result.stderr and "SYNTHETIC" not in result.stderr
    assert not output.exists() and not result.stdout.strip()


@pytest.mark.parametrize("payload", [None, [], "text", 42, {}, {"schema_version": "1.0"}])
def test_schema_validation_rejects_nonreport_json_cleanly(payload):
    with pytest.raises(ValueError, match="报告输入"):
        report_module().validate_payload(payload)


@pytest.mark.parametrize("mutation", [
    {"notes": float("nan")}, {"notes": float("inf")}, {"notes": {"nested": -float("inf")}},
    {"notes": {"x": set()}}, {"notes": {5: "not-json-key"}}, {"notes": "x" * 65537},
    {"notes": 1 << 300}, {"notes": [0] * 20001},
])
def test_full_input_shape_is_bounded_even_for_unshared_fields(mutation):
    payload = example("tarot")
    payload.update(mutation)
    with pytest.raises(ValueError, match="报告输入"):
        report_module().validate_json_shape(payload)
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


def test_full_input_shape_rejects_excessive_nesting():
    nested = "synthetic"
    for _ in range(26):
        nested = [nested]
    payload = example("tarot")
    payload["notes"] = nested
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


@pytest.mark.parametrize("warnings", [None, "text", {}, [None], [{}], ["x"] * 65, ["x" * 4097]])
def test_warning_contract_is_bounded_and_cleanly_rejected(warnings):
    payload = example("astrology")
    payload["warnings"] = warnings
    module = report_module()
    with pytest.raises(ValueError, match="报告输入"):
        module.safe_warnings(payload, "astrology")
    with pytest.raises(ValueError, match="报告输入"):
        module.render_report(payload)


def test_valid_json_shape_and_safe_warning_deduplication():
    payload = example("tarot")
    module = report_module()
    assert module.validate_json_shape(payload) is None
    payload["warnings"] = ["SYNTHETIC_SECRET", "SYNTHETIC_SECRET", "SYNTHETIC_OTHER_SECRET"]
    warnings = module.safe_warnings(payload, "tarot")
    assert len([warning for warning in warnings if "隐藏" in warning]) == 1
    assert "SYNTHETIC" not in repr(warnings)


@pytest.mark.parametrize("text", [
    '{"schema_version": "1.0", "schema_version": "1.0"}',
    '{"notes": NaN}', '{"notes": Infinity}', '{"notes": 1e999}',
    '[]', 'null', '{"notes": "SYNTHETIC_INVALID',
])
def test_json_reader_rejects_ambiguous_or_invalid_documents(tmp_path, text):
    source = tmp_path / "input.json"
    source.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="报告输入"):
        report_module().load_payload(source)
    result = run_report(source, tmp_path / "output.html")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr and "SYNTHETIC_INVALID" not in result.stderr
    assert not (tmp_path / "output.html").exists()


def test_json_reader_loads_one_requested_file_with_duplicate_key_guard():
    module = report_module()
    assert module.load_payload(ROOT / "examples" / "tarot-seeded.json") == example("tarot")
    assert module.unique_object([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}
    with pytest.raises(ValueError, match="报告输入"):
        module.unique_object([("a", 1), ("a", 2)])


def test_json_reader_limits_file_bytes_and_nesting_before_parsing(tmp_path):
    module = report_module()
    source = tmp_path / "large.json"
    source.write_text(" " * (module.MAX_INPUT_BYTES + 1), encoding="utf-8")
    with pytest.raises(ValueError, match="报告输入"):
        module.load_payload(source)
    source.write_text("[" * 1100 + "0" + "]" * 1100, encoding="utf-8")
    result = run_report(source, tmp_path / "result.html")
    assert result.returncode == 2 and "Traceback" not in result.stderr
    assert not (tmp_path / "result.html").exists()


def test_output_guard_accepts_only_explicit_html_in_user_or_ignored_directories(tmp_path):
    module = report_module()
    source = ROOT / "examples" / "tarot-seeded.json"
    assert module.checked_output_path(source, tmp_path / "report.html") == (tmp_path / "report.html").resolve()
    assert module.checked_output_path(source, ROOT / "private" / "report.html") == (ROOT / "private" / "report.html").resolve()
    assert module.checked_output_path(source, ROOT / "reports" / "report.html") == (ROOT / "reports" / "report.html").resolve()
    for destination in (ROOT / "report.html", ROOT / "examples" / "report.html", ROOT / "assets" / "report.html", ROOT / "private" / ".." / "report.html"):
        with pytest.raises(ValueError, match="追踪目录"):
            module.checked_output_path(source, destination)
    with pytest.raises(ValueError, match="HTML"):
        module.checked_output_path(source, tmp_path / "report.json")


def test_output_cannot_replace_source_even_with_overwrite(tmp_path):
    source = tmp_path / "input.html"
    original = json.dumps(example("tarot"), ensure_ascii=False)
    source.write_text(original, encoding="utf-8")
    result = run_report(source, source, "--overwrite")
    assert result.returncode == 2
    assert "输入" in result.stderr and "覆盖" in result.stderr
    assert source.read_text(encoding="utf-8") == original


def test_cli_refuses_project_tracked_directories_without_writing_them():
    assert hasattr(report_module(), "checked_output_path"), "Missing output-directory privacy guard"
    output = ROOT / "assets" / "report-unsafe-test.html"
    assert not output.exists()
    result = run_report(ROOT / "examples" / "tarot-seeded.json", output)
    assert result.returncode == 2 and "追踪目录" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("error", [
    NotImplementedError("symlinks unavailable"),
    OSError(errno.EPERM, "symlink privilege unavailable"),
    OSError(errno.EACCES, "symlink permission unavailable"),
    OSError(errno.ENOSYS, "symlink syscall unavailable"),
    OSError(errno.ENOTSUP, "symlinks unsupported on this filesystem"),
])
def test_symlink_fixture_skips_unsupported_creation(tmp_path, monkeypatch, symlink_factory, error):
    def unavailable(self, target, target_is_directory=False):
        raise error

    monkeypatch.setattr(Path, "symlink_to", unavailable)
    with pytest.raises(pytest.skip.Exception, match="symlink"):
        symlink_factory(tmp_path / "link.html", tmp_path / "target.html")


def test_symlink_fixture_skips_successful_call_without_a_symlink(tmp_path, monkeypatch, symlink_factory):
    def not_a_link(self, target, target_is_directory=False):
        self.write_text("SYNTHETIC_REGULAR_FILE", encoding="utf-8")

    monkeypatch.setattr(Path, "symlink_to", not_a_link)
    with pytest.raises(pytest.skip.Exception, match="symlink"):
        symlink_factory(tmp_path / "link.html", tmp_path / "target.html")


def test_symlink_fixture_does_not_hide_unexpected_os_errors(tmp_path, monkeypatch, symlink_factory):
    def unexpected(self, target, target_is_directory=False):
        raise OSError(errno.EIO, "SYNTHETIC_IO_ERROR")

    monkeypatch.setattr(Path, "symlink_to", unexpected)
    with pytest.raises(OSError, match="SYNTHETIC_IO_ERROR"):
        symlink_factory(tmp_path / "link.html", tmp_path / "target.html")


def test_output_symlink_cannot_modify_another_file(tmp_path, symlink_factory):
    target = tmp_path / "original.html"
    target.write_text("SYNTHETIC_UNTOUCHED", encoding="utf-8")
    output = tmp_path / "link.html"
    symlink_factory(output, target)
    result = run_report(ROOT / "examples" / "tarot-seeded.json", output, "--overwrite")
    assert result.returncode == 2
    assert target.read_text(encoding="utf-8") == "SYNTHETIC_UNTOUCHED"
    assert output.is_symlink()


def test_atomic_writer_does_not_change_hardlinked_original(tmp_path):
    module = report_module()
    original = tmp_path / "original.html"
    original.write_text("SYNTHETIC_UNTOUCHED", encoding="utf-8")
    output = tmp_path / "report.html"
    os.link(original, output)
    module.write_report(output, "<html>new report</html>", overwrite=True)
    assert original.read_text(encoding="utf-8") == "SYNTHETIC_UNTOUCHED"
    assert output.read_text(encoding="utf-8") == "<html>new report</html>"
    assert {path.name for path in tmp_path.iterdir()} == {"original.html", "report.html"}


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits do not verify Windows ACL privacy")
@pytest.mark.parametrize("scenario", ["tarot", "astrology", "hardlink-overwrite"])
def test_report_output_has_posix_private_permissions(tmp_path, scenario):
    output = tmp_path / "report.html"
    if scenario == "hardlink-overwrite":
        original = tmp_path / "original.html"
        original.write_text("SYNTHETIC_UNTOUCHED", encoding="utf-8")
        os.link(original, output)
        report_module().write_report(output, "<html>new report</html>", overwrite=True)
    else:
        input_path = ROOT / "examples" / {"tarot": "tarot-seeded.json", "astrology": "astrology-j2000.json"}[scenario]
        result = run_report(input_path, output)
        assert result.returncode == 0, result.stderr
    assert output.stat().st_mode & 0o777 == 0o600


def test_atomic_writer_requires_overwrite_and_removes_partial_files(tmp_path):
    module = report_module()
    output = tmp_path / "report.html"
    module.write_report(output, "original")
    with pytest.raises(FileExistsError):
        module.write_report(output, "new report")
    assert output.read_text(encoding="utf-8") == "original"
    with pytest.raises(UnicodeError):
        module.write_report(output, "\ud800", overwrite=True)
    assert output.read_text(encoding="utf-8") == "original"
    assert set(tmp_path.iterdir()) == {output}


def test_output_missing_parent_is_a_clean_error_not_a_traceback(tmp_path):
    output = tmp_path / "absent" / "report.html"
    result = run_report(ROOT / "examples" / "tarot-seeded.json", output)
    assert result.returncode == 2 and "Traceback" not in result.stderr
    assert not output.parent.exists()


@pytest.mark.parametrize("payload", [None, [], "text", 42, {}, {"schema_version": "9.0"}])
def test_astrology_validator_has_a_clean_direct_schema_error(payload):
    with pytest.raises(ValueError, match="报告输入"):
        report_module().validate_astrology(payload)


@pytest.mark.parametrize("change", [{"angles": "invalid", "houses": []}, {"angles": None, "houses": {}},
                                     {"time_known": "false"}, {"time_known": 0}, {"mode": "unverified-mode"}])
def test_astrology_rejects_invalid_mode_and_container_types(change):
    payload = example("astrology")
    payload.update(change)
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


@pytest.mark.parametrize("value", ["False", 0, 1, None])
def test_private_mode_must_be_an_explicit_boolean(value):
    with pytest.raises(ValueError, match="private"):
        report_module().render_report(example("tarot"), private=value)


@pytest.mark.parametrize("kind,key", [("tarot", "cards"), ("astrology", "bodies")])
def test_missing_required_calculated_record_fields_never_become_guessed_defaults(kind, key):
    payload = example(kind)
    record = payload[key][0] if kind == "tarot" else payload[key]["Sun"]
    record.pop("orientation" if kind == "tarot" else "house")
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


def test_astrology_without_location_still_requires_explicit_null_angles_and_houses():
    payload = example("astrology")
    payload.pop("angles")
    payload.pop("houses")
    for row in payload["bodies"].values():
        row["house"] = None
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


def test_report_schematic_styling_is_visible_and_tables_are_accessible():
    module = report_module()
    assert ".wheel{fill:none;" in module.STYLE
    assert ".body-marker{fill:" in module.STYLE
    assert ".angle-marker{stroke:" in module.STYLE
    assert ".house-cusp{stroke:" in module.STYLE
    assert "table{" in module.STYLE and "pre{" in module.STYLE
    for kind in ("tarot", "astrology"):
        document = module.render_report(example(kind))
        assert '<caption>' in document and 'scope="col"' in document
        assert 'role="img"' in document and 'aria-labelledby=' in document
        assert "不保证匿名" in document
        assert "viewport" in document


def test_equal_house_system_renders_the_real_cusps_and_house_numbers(tmp_path):
    computed = subprocess.run([sys.executable, str(ROOT / "scripts" / "astrology.py"),
                               "--datetime", "2000-01-01T12:00:00Z", "--lat", "39.9", "--lon", "116.4", "--houses", "equal"],
                              check=True, capture_output=True, text=True, timeout=20)
    payload = json.loads(computed.stdout)
    module = report_module()
    model = module.validate_payload(payload)
    svg = ET.fromstring(module.astrology_svg(model))
    cusps = svg.findall("s:line[@class='house-cusp']", NS)
    assert [float(node.attrib["data-longitude"]) for node in cusps] == pytest.approx(payload["houses"]["cusps"])
    assert "equal" in module.render_report(payload)
    assert model["bodies"]["Sun"]["house"] == payload["bodies"]["Sun"]["house"]


def test_real_date_range_engine_output_is_rejected_with_exit_two(tmp_path):
    computed = subprocess.run([sys.executable, str(ROOT / "scripts" / "astrology.py"),
                              "--date", "2000-01-01", "--timezone", "Asia/Shanghai"],
                             check=True, capture_output=True, text=True, timeout=20)
    payload = json.loads(computed.stdout)
    assert payload["mode"] == "unknown-time-day-range" and payload["bodies"] is None
    input_path = tmp_path / "real-range.json"
    input_path.write_text(computed.stdout, encoding="utf-8")
    output = tmp_path / "range.html"
    result = run_report(input_path, output)
    assert result.returncode == 2 and "不绘制单一星盘" in result.stderr
    assert "2000-01-01" not in result.stderr and "Asia/Shanghai" not in result.stderr
    assert not output.exists()


def test_omitted_house_is_invalid_even_when_no_location_was_calculated():
    payload = example("astrology")
    payload.update(angles=None, houses=None, location=None)
    for row in payload["bodies"].values():
        row["house"] = None
    payload["bodies"]["Sun"].pop("house")
    with pytest.raises(ValueError, match="报告输入"):
        report_module().render_report(payload)


def test_warning_mapping_rejects_nondictionary_input_without_traceback():
    with pytest.raises(ValueError, match="报告输入"):
        report_module().safe_warnings(None, "tarot")


def test_cyclic_output_parent_symlink_is_a_clean_cli_error(tmp_path, symlink_factory):
    parent = tmp_path / "loop"
    symlink_factory(parent, parent, target_is_directory=True)
    result = run_report(ROOT / "examples" / "tarot-seeded.json", parent / "report.html")
    assert result.returncode == 2 and "Traceback" not in result.stderr


def test_escaped_unpaired_surrogate_is_cleanly_rejected_before_output(tmp_path):
    payload = example("tarot")
    payload["notes"] = "\ud800"
    source = tmp_path / "input.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    module = report_module()
    with pytest.raises(ValueError, match="报告输入"):
        module.load_payload(source)
    for flags in ([], ["--private"]):
        result = run_report(source, tmp_path / "result.html", *flags)
        assert result.returncode == 2 and "Traceback" not in result.stderr
        assert not (tmp_path / "result.html").exists()


def test_json_reader_rejects_special_device_instead_of_reading_it():
    with pytest.raises(ValueError, match="普通文件"):
        report_module().load_payload(Path(os.devnull))


def test_share_svg_numeric_attributes_reject_url_and_filename_injection(tmp_path):
    payload = example("astrology")
    payload["bodies"]["Sun"]["longitude"] = '0" onclick="alert(1)" href="file:///SYNTHETIC_SECRET'
    source = tmp_path / "attack.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = run_report(source, tmp_path / "attack.html")
    assert result.returncode == 2 and "报告输入" in result.stderr
    assert "SYNTHETIC_SECRET" not in result.stderr and "onclick" not in result.stderr
    assert not (tmp_path / "attack.html").exists()


def test_report_writer_remains_usable_without_posix_fchmod(tmp_path, monkeypatch):
    module = report_module()
    monkeypatch.delattr(module.os, "fchmod", raising=False)
    output = tmp_path / "portable.html"
    module.write_report(output, "<html>portable synthetic report</html>")
    assert output.read_text(encoding="utf-8") == "<html>portable synthetic report</html>"
