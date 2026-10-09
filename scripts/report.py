#!/usr/bin/env python3
"""Offline, input-only report renderer; no calculations or interpretations."""
import argparse
from html import escape
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

SIGNS = "白羊座 金牛座 双子座 巨蟹座 狮子座 处女座 天秤座 天蝎座 射手座 摩羯座 水瓶座 双鱼座".split()
BODIES = {"Sun": "太阳", "Moon": "月亮", "Mercury": "水星", "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星"}
MAJORS = "愚者 魔术师 女祭司 女皇 皇帝 教皇 恋人 战车 力量 隐士 命运之轮 正义 倒吊人 死神 节制 恶魔 高塔 星星 月亮 太阳 审判 世界".split()
DECK = MAJORS + [suit + rank for suit in ("权杖", "圣杯", "宝剑", "星币")
                 for rank in "王牌 二 三 四 五 六 七 八 九 十 侍从 骑士 王后 国王".split()]
SPREADS = {
    "single": ["当前指引"], "three": ["过去", "现在", "可能走向"],
    "diamond": ["核心", "根源", "阻力", "潜力", "建议"],
    "moon": ["新月", "上弦", "满月", "下弦"],
    "horseshoe": ["远期过去", "近期过去", "当前", "近期走向", "外部影响", "建议", "可能结果"],
    "celtic": ["核心", "交叉", "意识目标", "根基", "近期过去", "近期走向", "自我", "环境", "希望与恐惧", "可能结果"],
}
INPUT_ERROR = "报告输入不符合受支持的计算 JSON；请核验版本、字段与数值。"
MAX_INPUT_BYTES = 1024 * 1024
MAX_DEPTH = 24
MAX_NODES = 20000


def validate_json_shape(payload):
    """Bound all JSON data (also ignored fields) and reject nonfinite numbers."""
    stack = [(payload, 0)]
    count = 0
    while stack:
        value, depth = stack.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError(INPUT_ERROR)
        if isinstance(value, dict):
            if len(value) > MAX_NODES - count:
                raise ValueError(INPUT_ERROR)
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > 65536:
                    raise ValueError(INPUT_ERROR)
                if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                    raise ValueError(INPUT_ERROR)
                stack.append((child, depth + 1))
        elif isinstance(value, list):
            if len(value) > MAX_NODES - count:
                raise ValueError(INPUT_ERROR)
            stack.extend((child, depth + 1) for child in value)
        elif isinstance(value, str):
            if len(value) > 65536 or any(0xD800 <= ord(char) <= 0xDFFF for char in value):
                raise ValueError(INPUT_ERROR)
        elif type(value) is int:
            if value.bit_length() > 256:
                raise ValueError(INPUT_ERROR)
        elif type(value) is float:
            if not math.isfinite(value):
                raise ValueError(INPUT_ERROR)
        elif value is not None and type(value) is not bool:
            raise ValueError(INPUT_ERROR)


def unique_object(pairs):
    """Do not silently pick one value from a duplicate JSON key."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(INPUT_ERROR)
        result[key] = value
    return result


def load_payload(path):
    """Read at most one MiB from the explicitly requested local input only."""
    if not Path(path).is_file():
        raise ValueError("输入必须为本地普通文件；不读取设备、管道或目录。")
    with Path(path).open("rb") as source:
        raw = source.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(INPUT_ERROR)
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        validate_payload(payload)
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError):
        raise ValueError(INPUT_ERROR) from None
    return payload


def validate_payload(payload):
    """Validate the result contract and project only approved shared data."""
    validate_json_shape(payload)
    if not isinstance(payload, dict) or payload.get("schema_version") not in ("1.0", "1.1"):
        raise ValueError(INPUT_ERROR)
    safe_warnings(payload, "tarot")  # validate structure before any rendering
    fields = [key for key in ("cards", "bodies", "pillars") if key in payload]
    if len(fields) != 1:
        raise ValueError(INPUT_ERROR)
    kind = {"cards": "tarot", "bodies": "astrology", "pillars": "bazi"}[fields[0]]
    if payload.get("system", kind) != kind:
        raise ValueError(INPUT_ERROR)
    if kind == "astrology":
        return validate_astrology(payload)
    if kind != "tarot":
        raise ValueError("八字报告未支持；请使用原始计算 JSON 核验，不生成替代盘面。")
    spread = payload.get("spread")
    if not isinstance(spread, str) or spread not in SPREADS:
        raise ValueError(INPUT_ERROR)
    rows = payload["cards"]
    if not isinstance(rows, list) or len(rows) != len(SPREADS[spread]):
        raise ValueError(INPUT_ERROR)
    if (payload.get("deck") != "Rider-Waite-Smith; Strength VIII; Justice XI"
            or payload.get("algorithm") != "uniform-without-replacement"
            or payload.get("randomness") not in ("system-random", "seeded-pseudorandom")):
        raise ValueError(INPUT_ERROR)
    probability = payload.get("reversed_probability")
    if type(probability) not in (float, int) or not 0 <= probability <= 1 or not math.isfinite(probability):
        raise ValueError(INPUT_ERROR)
    cards = []
    for row, position in zip(rows, SPREADS[spread]):
        if (not isinstance(row, dict) or row.get("position") != position
                or row.get("card") not in DECK or row.get("orientation") not in ("正位", "逆位")
                or type(row.get("is_major")) is not bool
                or row["is_major"] != (row["card"] in MAJORS)):
            raise ValueError(INPUT_ERROR)
        cards.append({key: row[key] for key in ("position", "card", "orientation")})
    if len({row["card"] for row in cards}) != len(cards):
        raise ValueError(INPUT_ERROR)
    return {"kind": "tarot", "spread": spread, "cards": cards,
            "conventions": f'{payload["deck"]} · {payload["algorithm"]} · {payload["randomness"]} · 逆位概率 {probability:g}'}


def validate_astrology(payload):
    """Check ten-body tropical whole/equal-sign data without recalculating it."""
    validate_json_shape(payload)
    if (not isinstance(payload, dict) or payload.get("schema_version") not in ("1.0", "1.1")
            or payload.get("system", "astrology") != "astrology"):
        raise ValueError(INPUT_ERROR)
    if payload.get("mode") == "unknown-time-day-range" or payload.get("time_known") is False or "body_ranges" in payload:
        raise ValueError("未知生时日内范围报告未支持；不绘制单一星盘，请私下核验原始范围 JSON。")
    if (("time_known" in payload and payload["time_known"] is not True)
            or "mode" in payload or "angles" not in payload or "houses" not in payload):
        raise ValueError(INPUT_ERROR)
    if (payload.get("zodiac") != "tropical"
            or payload.get("frame") != "geocentric-apparent-ecliptic-of-date"):
        raise ValueError(INPUT_ERROR)
    engine = payload.get("engine")
    if (not isinstance(engine, dict) or engine.get("name") != "astronomy-engine"
            or not isinstance(engine.get("version"), str)
            or re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", engine["version"]) is None):
        raise ValueError(INPUT_ERROR)
    bodies = payload.get("bodies")
    if not isinstance(bodies, dict) or set(bodies) != set(BODIES):
        raise ValueError(INPUT_ERROR)
    angles, houses = payload.get("angles"), payload.get("houses")
    if (angles is None) != (houses is None):
        raise ValueError(INPUT_ERROR)
    first = None
    if angles is not None:
        if not isinstance(angles, dict) or set(angles) != {"ASC", "DSC", "MC", "IC"}:
            raise ValueError(INPUT_ERROR)
        for value in angles.values():
            if type(value) not in (int, float) or not 0 <= value < 360 or not math.isfinite(value):
                raise ValueError(INPUT_ERROR)
        if (not math.isclose(angles["DSC"], (angles["ASC"] + 180) % 360, abs_tol=1e-7)
                or not math.isclose(angles["IC"], (angles["MC"] + 180) % 360, abs_tol=1e-7)):
            raise ValueError(INPUT_ERROR)
        if not isinstance(houses, dict) or houses.get("system") not in ("whole-sign", "equal"):
            raise ValueError(INPUT_ERROR)
        cusps = houses.get("cusps")
        if not isinstance(cusps, list) or len(cusps) != 12:
            raise ValueError(INPUT_ERROR)
        first = math.floor(angles["ASC"] / 30) * 30 if houses["system"] == "whole-sign" else angles["ASC"]
        for index, value in enumerate(cusps):
            if (type(value) not in (float, int) or not 0 <= value < 360 or not math.isfinite(value)
                    or not math.isclose(value, (first + index * 30) % 360, abs_tol=1e-7)):
                raise ValueError(INPUT_ERROR)
    shared_bodies = {}
    for key, label in BODIES.items():
        row = bodies[key]
        if not isinstance(row, dict) or "house" not in row:
            raise ValueError(INPUT_ERROR)
        longitude, degree = row.get("longitude"), row.get("sign_degree")
        if (type(longitude) not in (int, float) or not 0 <= longitude < 360 or not math.isfinite(longitude)
                or type(degree) not in (float, int) or not 0 <= degree < 30 or not math.isfinite(degree)
                or not math.isclose(degree, longitude % 30, abs_tol=1e-7)
                or row.get("name") != label or row.get("sign") != SIGNS[int(longitude // 30)]):
            raise ValueError(INPUT_ERROR)
        house = row.get("house")
        expected = None if first is None else int(((longitude - first) % 360) // 30) + 1
        if house != expected or (expected is not None and type(house) is not int):
            raise ValueError(INPUT_ERROR)
        shared_bodies[key] = {"name": label, "longitude": longitude, "sign": row["sign"], "sign_degree": degree, "house": house}
    return {"kind": "astrology", "bodies": shared_bodies,
            "angles": None if angles is None else {key: angles[key] for key in ("ASC", "DSC", "MC", "IC")},
            "houses": None if houses is None else {"system": houses["system"], "cusps": list(houses["cusps"])},
            "conventions": 'tropical · geocentric-apparent-ecliptic-of-date · astronomy-engine '
            + engine["version"] + (' · ' + houses["system"] if houses is not None else ' · 未计算宫位')}


def safe_warnings(payload, kind):
    """Map exact known warnings to fixed safe text; hide all unknown wording."""
    if not isinstance(payload, dict):
        raise ValueError(INPUT_ERROR)
    incoming = payload.get("warnings", [])
    if (not isinstance(incoming, list) or len(incoming) > 64
            or any(not isinstance(warning, str) or len(warning) > 4096 for warning in incoming)):
        raise ValueError(INPUT_ERROR)
    common = "仅供文化研究、娱乐与自我反思；计算结果不证明命运预测有效。"
    mapping = {
        "占星解释仅供文化研究、娱乐与自我反思；天体位置的可计算性不证明命运预测有效。": "天体位置可计算，但不证明命运预测有效。",
        "高纬度上升点变化特殊，仅支持整宫/等宫；勿按每两小时一星座推断。": "高纬度角点可能变化特殊；本报告只支持整宫/等宫。",
        "未提供经纬度，未计算上升、天顶与宫位。": "输入未计算角点与宫位；本报告不补算。",
        "公农历换算采用 lunar-python；四柱与起运使用的节气时刻仍为简式近似，交界请用独立历书交叉核验。": "四柱节气口径为简式近似，交界须独立历书核验。",
        "固定北京时间；未做历史夏令时、海外时区或真太阳时校正。": "固定民用时区口径，未作历史夏令时、海外时区或真太阳时校正。",
    }
    result = [common]
    if kind == "tarot":
        result.append("牌面为程序生成的示意牌框，不是原版牌画；不包含自动解读。")
    else:
        result.append("星盘仅展示输入中的十天体静态位置与已计算角点；不生成相位解读或新计算。")
    for warning in payload.get("warnings", []):
        safe = mapping.get(warning, "输入含未识别注意事项；为保护隐私已隐藏原文，请私下核验原始 JSON。")
        if safe not in result:
            result.append(safe)
    return result


STYLE = """
:root{color-scheme:light;--ink:#241f32;--paper:#f5f2f9;--accent:#65429a;--line:#c9bfd9}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1000px;margin:auto;padding:36px 24px}header{border-bottom:1px solid var(--line);margin-bottom:28px}
h1{font-size:clamp(28px,5vw,44px);line-height:1.2}h2{font-size:23px}.eyebrow{letter-spacing:.12em;color:var(--accent)}
section{margin:28px 0;padding:22px;background:#fff;border:1px solid var(--line);border-radius:16px}
svg{display:block;max-width:100%;height:auto;margin:auto}svg text{fill:var(--ink);font-family:system-ui,sans-serif}
.card-face{fill:#f5f2f9;stroke:#65429a;stroke-width:2}.card-mark{fill:none;stroke:#65429a;stroke-width:1.5}
.caption{text-anchor:middle;font-size:16px}.small{font-size:14px}.notice{border-left:4px solid var(--accent);padding-left:16px}
.wheel{fill:none;stroke:#88779e;stroke-width:1.5}.zodiac-tick{stroke:#ddd5e8;stroke-width:1}
.house-cusp{stroke:#9b8aae;stroke-width:1;stroke-dasharray:3 4}.angle-marker{stroke:#65429a;stroke-width:2}
.body-marker{fill:#65429a;stroke:#fff;stroke-width:1.5}.sign-label,.house-label,.angle-label,.body-label{text-anchor:middle;dominant-baseline:middle;font-size:15px}
.angle-label{font-weight:700}.body-label{font-weight:600}.house-label{font-size:14px}
table{width:100%;border-collapse:collapse;margin-top:24px}caption{text-align:left;font-weight:600;margin-bottom:12px}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{font-size:14px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;font:14px/1.6 ui-monospace,monospace}.private{border:2px solid var(--accent)}
@media(max-width:480px){main{padding:24px 12px}section{padding:14px}th,td{padding:8px 4px}}
@media print{body{background:#fff}main{padding:12px}section{break-inside:avoid}svg{max-height:650px}}
"""


def tarot_svg(model):
    """Draw validated cards using fixed local layouts, never input CSS or URLs."""
    spread = model["spread"]
    layouts = {
        "single": (160, 320, [(24, 48)]),
        "three": (510, 320, [(24, 48), (194, 48), (364, 48)]),
        "diamond": (612, 880, [(250, 330), (250, 48), (24, 330), (476, 330), (250, 612)]),
        "moon": (612, 602, [(24, 48), (194, 330), (364, 330), (476, 48)]),
        "horseshoe": (920, 880, [(24, 48), (130, 330), (250, 612), (404, 612), (558, 612), (678, 330), (784, 48)]),
        "celtic": (930, 1190, [(285, 420), (315, 435), (285, 100), (285, 740), (50, 420), (520, 420),
                              (760, 900), (760, 620), (760, 340), (760, 60)]),
    }
    width, height, slots = layouts[spread]
    cards = []
    for index, (row, (x, y)) in enumerate(zip(model["cards"], slots)):
        orientation = row["orientation"]
        rotation = "rotate(180 56 85)" if orientation == "逆位" else "rotate(0 56 85)"
        if spread == "celtic" and index == 1:
            rotation = "rotate(90 56 85) " + rotation
        cards.append(
            f'<g class="tarot-card" data-card="{escape(row["card"], quote=True)}" '
            f'data-orientation="{escape(orientation, quote=True)}" transform="translate({x} {y})">'
            f'<title>{escape(row["position"] + "：" + row["card"] + " · " + orientation, quote=True)}</title>'
            f'<g transform="{rotation}"><rect class="card-face" width="112" height="170" rx="12"/>'
            '<rect class="card-mark" x="10" y="10" width="92" height="150" rx="8"/>'
            '<circle class="card-mark" cx="56" cy="74" r="25"/>'
            f'<text class="caption" x="56" y="81">{index + 1}</text>'
            '<path class="card-mark" d="M56 23L61 34L56 45L51 34Z"/></g>'
            f'<text class="caption" x="56" y="-16">{escape(row["position"], quote=True)}</text>'
            f'<text class="caption" x="56" y="199">{escape(row["card"], quote=True)}</text>'
            f'<text class="caption small" x="56" y="225">{escape(orientation, quote=True)}</text></g>'
        )
    return ('<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="spread-title" '
            f'viewBox="0 0 {width} {height}"><title id="spread-title">塔罗牌阵 · {spread}</title>'
            '<desc>数字对应下方牌位表；逆位牌框旋转180度。凯尔特第二张横置表示交叉位置。</desc>'
            + ''.join(cards) + '</svg>')


def astrology_svg(model):
    """Plot supplied ecliptic longitudes (Aries left, increasing counterclockwise)."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="chart-title" viewBox="0 0 720 720">',
        '<title id="chart-title">基础星盘 · 十天体与已计算角点</title>',
        '<desc>白羊座零度在左，黄经逆时针增加；点位角度来自输入，径向错层仅为避免标签重叠。完整数值见表。</desc>',
        '<circle class="wheel" cx="360" cy="360" r="280"/>',
        '<circle class="wheel" cx="360" cy="360" r="250"/>',
        '<circle class="wheel" cx="360" cy="360" r="105"/>',
    ]
    for index, sign in enumerate(SIGNS):
        angle = math.radians(index * 30)
        x, y = 360 - 280 * math.cos(angle), 360 + 280 * math.sin(angle)
        parts.append(f'<line class="zodiac-tick" x1="360" y1="360" x2="{x:.3f}" y2="{y:.3f}"/>')
        middle = math.radians(index * 30 + 15)
        x, y = 360 - 305 * math.cos(middle), 360 + 305 * math.sin(middle)
        parts.append(f'<text class="sign-label" x="{x:.3f}" y="{y:.3f}">{escape(sign, quote=True)}</text>')
    if model["houses"] is not None:
        for index, longitude in enumerate(model["houses"]["cusps"]):
            angle = math.radians(longitude)
            x, y = 360 - 245 * math.cos(angle), 360 + 245 * math.sin(angle)
            parts.append(f'<line class="house-cusp" data-house="{index + 1}" data-longitude="{longitude}" '
                         f'x1="360" y1="360" x2="{x:.3f}" y2="{y:.3f}"/>')
            middle = math.radians((longitude + 15) % 360)
            x, y = 360 - 85 * math.cos(middle), 360 + 85 * math.sin(middle)
            parts.append(f'<text class="house-label" x="{x:.3f}" y="{y:.3f}">{index + 1}</text>')
    if model["angles"] is not None:
        for label, longitude in model["angles"].items():
            angle = math.radians(longitude)
            x, y = 360 - 250 * math.cos(angle), 360 + 250 * math.sin(angle)
            parts.append(f'<line class="angle-marker" data-angle="{label}" data-longitude="{longitude}" '
                         f'x1="360" y1="360" x2="{x:.3f}" y2="{y:.3f}"><title>{label} {longitude:.6f}°</title></line>')
            x, y = 360 - 266 * math.cos(angle), 360 + 266 * math.sin(angle)
            parts.append(f'<text class="angle-label" x="{x:.3f}" y="{y:.3f}">{label}</text>')
    for index, (key, row) in enumerate(model["bodies"].items()):
        longitude = row["longitude"]
        radius = 146 + (index % 3) * 27
        angle = math.radians(longitude)
        x, y = 360 - radius * math.cos(angle), 360 + radius * math.sin(angle)
        parts.append(f'<circle class="body-marker" data-body="{key}" data-longitude="{longitude}" data-radius="{radius}" '
                     f'cx="{x:.3f}" cy="{y:.3f}" r="5"><title>{escape(row["name"], quote=True)} {longitude:.6f}°</title></circle>')
        x, y = 360 - (radius + 14) * math.cos(angle), 360 + (radius + 14) * math.sin(angle)
        parts.append(f'<text class="body-label" x="{x:.3f}" y="{y:.3f}">{index + 1}</text>')
    return ''.join(parts) + '</svg>'


def render_report(payload, private=False):
    """Produce a self-contained report solely from validated result fields."""
    if type(private) is not bool:
        raise ValueError("private 必须显式为布尔值；默认为分享版。")
    model = validate_payload(payload)
    if model["kind"] == "tarot":
        title = "塔罗牌阵"
        svg = tarot_svg(model)
        table_rows = ''.join('<tr><td>' + escape(row["position"], quote=True) + '</td><td>'
                             + escape(row["card"], quote=True) + '</td><td>'
                             + escape(row["orientation"], quote=True) + '</td></tr>' for row in model["cards"])
        table = '<table><caption>抽牌结果</caption><thead><tr><th scope="col">牌位</th><th scope="col">牌名</th><th scope="col">正逆位</th></tr></thead><tbody>' + table_rows + '</tbody></table>'
    else:
        title = "基础星盘"
        svg = astrology_svg(model)
        table_rows = ''.join(f'<tr><td>{index + 1} · {escape(row["name"], quote=True)}</td><td>'
                             + escape(row["sign"], quote=True) + f' {row["sign_degree"]:.6f}°</td><td>'
                             + ('未计算' if row["house"] is None else f'第{row["house"]}宫') + '</td></tr>'
                             for index, row in enumerate(model["bodies"].values()))
        table = '<table><caption>十天体静态位置 · 数字对应图中标记</caption><thead><tr><th scope="col">天体</th><th scope="col">星座内度数</th><th scope="col">宫位</th></tr></thead><tbody>' + table_rows + '</tbody></table>'
        if model["angles"] is not None:
            table += '<p>角点：' + ' · '.join(f'{key} {value:.6f}°' for key, value in model["angles"].items()) + '</p>'
    warnings = '<section><h2>Warnings / 注意事项</h2><ul>' + ''.join(
        '<li>' + escape(warning, quote=True) + '</li>' for warning in safe_warnings(payload, model["kind"])) + '</ul></section>'
    mode = "私密版 · 包含原始输入，不可公开分享。" if private else "分享版 · 已隐藏原始问题与出生资料；派生结果仍不保证匿名。"
    original = ''
    if private:
        original = ('<section class="private"><h2>原始输入 · 不可公开分享</h2><p>此文件含输入中的问题、姓名、出生资料或备注；请仅本地保存。</p>'
                    '<pre id="original-input">' + escape(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), quote=True) + '</pre></section>')
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'none\'; connect-src \'none\'; img-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Lilith · 本地报告</title><style>' + STYLE + '</style></head><body><main>'
            '<header><p class="eyebrow">LILITH / LOCAL REPORT</p><h1>' + title + '</h1>'
            '<p class="notice">' + mode + '</p><p>仅展示已有计算结果，不生成解读。</p></header><section><h2>结果与图示</h2>' + svg + table +
            '</section><section><h2>计算口径</h2><p>' + escape(model["conventions"], quote=True) + '</p></section>'
            + warnings + original + '</main></body></html>')


def checked_output_path(input_path, output_path):
    """Keep personal reports out of project source directories and source files."""
    output = Path(output_path).absolute()
    if output.is_symlink():
        raise ValueError("输出不能是符号链接；请指定独立 HTML 文件。")
    destination = output.resolve()
    if destination.suffix.lower() not in (".html", ".htm"):
        raise ValueError("输出必须为 HTML 文件（.html 或 .htm）。")
    source = Path(input_path).resolve()
    if destination == source or (destination.exists() and source.exists() and os.path.samefile(destination, source)):
        raise ValueError("不能用报告覆盖输入文件；请指定不同的输出 HTML。")
    root = Path(__file__).resolve().parents[1]
    if destination.is_relative_to(root):
        relative = destination.relative_to(root)
        if len(relative.parts) < 2 or relative.parts[0] not in ("private", "reports"):
            raise ValueError("不能将个人报告写入项目追踪目录；请使用 private/、reports/ 或仓库外目录。")
    return destination


def write_report(output, document, overwrite=False):
    """Publish complete HTML atomically without following file links.

    Files have mode 0600 on POSIX; Windows privacy depends on filesystem ACLs.
    """
    output = Path(output)
    if output.is_symlink():
        raise ValueError("输出不能是符号链接；请指定独立 HTML 文件。")
    if output.exists() and not overwrite:
        raise FileExistsError
    if output.exists() and not output.is_file():
        raise ValueError("输出必须是独立 HTML 文件。")
    descriptor, name = tempfile.mkstemp(prefix=".lilith-report-", suffix=".tmp", dir=output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            # mkstemp already creates mode 0600 on POSIX; Windows privacy depends on its ACL.
            target.write(document)
            target.flush()
            os.fsync(target.fileno())
        if overwrite:
            os.replace(temporary, output)
        else:
            os.link(temporary, output)  # atomic exclusive publish, even if another writer won
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    """Read one explicit JSON, write one explicit HTML, and report safe errors."""
    parser = argparse.ArgumentParser(description="离线自包含 HTML 报告；默认隐藏问题与出生原始资料")
    parser.add_argument("--input", required=True, help="已有计算 JSON 文件")
    parser.add_argument("--output", required=True, help="用户自行指定的 HTML 路径；推荐 private/ 或仓库外目录")
    parser.add_argument("--private", action="store_true", help="显式在 HTML 中包含原始输入；不可公开分享")
    parser.add_argument("--overwrite", action="store_true", help="显式允许覆盖已有报告")
    args = parser.parse_args(argv)
    try:
        payload = load_payload(args.input)
        document = render_report(payload, private=args.private)
    except (OSError, UnicodeError, json.JSONDecodeError):
        parser.error("无法读取输入 JSON；请核验文件与 UTF-8 编码。")
    except ValueError as error:
        parser.error(str(error))
    try:
        output = checked_output_path(args.input, args.output)
        write_report(output, document, overwrite=args.overwrite)
    except FileExistsError:
        parser.error("输出已存在；如需覆盖，请显式指定 --overwrite。")
    except (OSError, UnicodeError, RuntimeError):
        parser.error("无法写入输出 HTML；请核验父目录与权限。")
    except ValueError as error:
        parser.error(str(error))
    if args.private:
        print("私密版包含原始输入，不可公开分享。", file=sys.stderr)
    print("已写入本地 HTML 报告。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
