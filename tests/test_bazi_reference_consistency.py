"""Offline reference-contract regressions; no network or vendor writes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references" / "bazi"


def test_dayun_documents_unrounded_engine_contract():
    text = (REFERENCES / "dayun-rules.md").read_text(encoding="utf-8")
    assert "四舍五入到最接近的整数岁数" not in text
    for token in ("lunar-python 1.4.8", "getYun", "sect=2", "start_age",
                  "years", "months", "days", "hours", "start_solar",
                  "UTC+08:00", "nominal-year-age", "不是周岁", "dayun=null"):
        assert token in text, token
    assert "不四舍五入" in text
    assert "小运" in text and "占位" in text


def test_wuxing_months_use_jie_boundaries_not_lunar_month_numbers():
    text = (REFERENCES / "wuxing-tables.md").read_text(encoding="utf-8")
    assert "月份（农历）" not in text
    assert "节令月" in text and "不是农历月份" in text
    for branch, start, end in (("寅", "立春", "惊蛰"), ("卯", "惊蛰", "清明"),
                               ("辰", "清明", "立夏"), ("巳", "立夏", "芒种"),
                               ("午", "芒种", "小暑"), ("未", "小暑", "立秋"),
                               ("申", "立秋", "白露"), ("酉", "白露", "寒露"),
                               ("戌", "寒露", "立冬"), ("亥", "立冬", "大雪"),
                               ("子", "大雪", "小寒"), ("丑", "小寒", "立春")):
        row = next(line for line in text.splitlines() if line.startswith(f"| {branch} |"))
        assert start in row and end in row, row
    assert "absolute-instant" in text


def test_wuxing_does_not_supply_unsourced_exact_strength_weights():
    text = (REFERENCES / "wuxing-tables.md").read_text(encoding="utf-8")
    assert "力量减半" not in text
    assert not re.search(r"(?:60|30|10)\s*%", text)
    assert "不提供数值权重" in text
    assert "不是量化比例" in text


def test_shichen_requires_confirmation_and_honest_cli_limits():
    text = (REFERENCES / "shichen-table.md").read_text(encoding="utf-8")
    for unsafe in ("| 天刚亮 / 早上 | 卯时 |", "| 吃早饭 / 上午 | 辰时 |"):
        assert unsafe not in text
    for token in ("天刚亮", "吃早饭", "追问", "确认", "range", "未知",
                  "不支持任意时间范围", "分别", "--shichen", "--hour", "dayun=null",
                  "23:00", "sect=1", "当地民用"):
        assert token in text, token
    assert "不能把日出或用餐习惯当作钟点" in text


def test_classical_quotes_distinguish_transcription_commentary_and_simplification():
    text = (REFERENCES / "classical-texts.md").read_text(encoding="utf-8")
    assert "旺极宜泄不宜克，衰极宜扶不宜帮" not in text
    assert "寅上起月，顺数至生时，所落之宫即为命宫" not in text
    for token in ("作者简化", "unverified", "电子转录", "不是影印校勘",
                  "衰旺論", "原注", "任氏", "專求月令", "格局用神",
                  "不是统一的最有利五行", "docs/bazi-reference-audit.md"):
        assert token in text, token
    assert "旺之極者不可損" in text and "衰之極者不可益" in text
    assert "衰极宜扶" not in text


def test_audit_records_actual_read_sections_and_limitations():
    import json
    from datetime import datetime
    path = ROOT / "docs" / "bazi-reference-audit.md"
    assert path.is_file(), "Missing consulted-source audit"
    text = path.read_text(encoding="utf-8")
    block = re.search(r"```json\n(.*?)\n```", text, re.S)
    assert block, "Source metadata must be machine-checkable"
    records = json.loads(block.group(1))
    assert len(records) >= 6
    assert len({record["url"] for record in records}) == len(records)
    for record in records:
        assert record["url"].startswith("https://")
        assert record["title"] and record["sections_read"]
        datetime.fromisoformat(record["accessed_at"])
        assert record["coverage"] in ("section-complete", "partial", "file-complete")
    assert "未核对底本" in text and "unverified" in text
    assert "先红后绿" in text and "不支持任意时间范围" in text
    assert "/home/" not in text
