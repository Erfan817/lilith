#!/usr/bin/env python3
"""Unified BaZi JSON interface with explicit calendar uncertainty."""
import argparse
from datetime import date, datetime
import importlib.util
import json
from pathlib import Path


def calendar_engine(filename="vendor/bazi/pai_pan.py", name="mystic_calendar_engine"):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    engine = calendar_engine()
    parser = argparse.ArgumentParser(description="八字排盘：明确历法与时区口径，JSON 输出")
    parser.add_argument("--solar", help="公历 YYYY-MM-DD")
    parser.add_argument("--lunar", help="农历 YYYY-MM-DD（不是公历日期有效性规则）")
    parser.add_argument("--leap", action="store_true", help="农历闰月")
    hours = parser.add_mutually_exclusive_group()
    hours.add_argument("--hour", help="民用钟表时间 HH:MM；默认固定北京时间，可用 --timezone 指定当地时区")
    parser.add_argument("--timezone", help="当地 IANA 时区，如 Asia/Shanghai；省略为固定 UTC+08:00")
    parser.add_argument("--fold", type=int, choices=(0, 1), help="回拨歧义时刻：0 第一次，1 第二次")
    parser.add_argument("--time-basis", choices=("civil", "apparent-solar"), default="civil", help="日/时柱时间口径；默认民用时，视太阳时须显式选择")
    parser.add_argument("--longitude", type=float, help="视太阳时经度；东经为正，需 --time-basis apparent-solar 与确定钟点")
    hours.add_argument("--shichen", choices=list(engine.ZHI))
    parser.add_argument("--sex", choices=("男", "女"), help="传统大运顺逆参数；省略则不输出大运")
    parser.add_argument("--place", help="出生城市；仅展示与风险提示")
    parser.add_argument("--deceased-year", type=int, help="用户已声明的逝世年份，流年截止该年")
    parser.add_argument("--as-of", help="流年截止公历日期 YYYY-MM-DD；省略则用实际当前日期")
    args = parser.parse_args()
    try:
        from lunar_python import Lunar, Solar
        compute = calendar_engine("bazi_engine.py", "lilith_bazi_engine").compute
        if not args.solar and not args.lunar:
            raise ValueError("至少提供 --solar 或 --lunar")
        if args.hour and args.shichen:
            raise ValueError("--hour 与 --shichen 互斥")
        if args.leap and not args.lunar:
            raise ValueError("--leap 只能与 --lunar 同时使用")
        if args.deceased_year is not None and not 1900 <= args.deceased_year <= 2100:
            raise ValueError("逝世年份需 1900–2100")
        solar_date = engine.parse_iso_date(args.solar, "--solar") if args.solar else None
        if args.lunar:
            parts = args.lunar.split("-")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                raise ValueError("农历需要 YYYY-MM-DD 数字格式")
            ly, lm, ld = map(int, parts)
            if not 1900 <= ly <= 2100 or not 1 <= lm <= 12 or not 1 <= ld <= 30:
                raise ValueError("农历年份需 1900–2100，月1–12，日1–30")
            try:
                lunar_date = Lunar.fromYmd(ly, -lm if args.leap else lm, ld)
            except Exception as exc:
                # lunar-python 1.4.8 uses plain Exception for invalid lunar dates.
                if type(exc) is not Exception:
                    raise
                raise ValueError("农历日期或闰月无效：%s" % exc) from exc
            solar = lunar_date.getSolar()
            converted = date(solar.getYear(), solar.getMonth(), solar.getDay())
            if solar_date is not None and converted != solar_date:
                raise ValueError("公历与农历输入不一致，请核验日期")
            solar_date = converted
        if not 1900 <= solar_date.year <= 2100:
            raise ValueError("支持年份为 1900–2100")
        lunar_date = Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day).getLunar()
        lunar_month = lunar_date.getMonth()
        display = engine.format_lunar(lunar_date.getYear(), abs(lunar_month), lunar_date.getDay(), lunar_month < 0)
        if args.deceased_year is not None and args.deceased_year < solar_date.year:
            raise ValueError("逝世年份不能早于出生年份")
        hour, minute = engine.parse_hour(args.hour) if args.hour else (None, None)
        as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(engine.BJ).date()
        if not 1900 <= as_of.year <= 2100:
            raise ValueError("分析年份需 1900–2100")
        if as_of < solar_date:
            raise ValueError("分析日期不能早于出生日期")
        now = datetime(as_of.year, as_of.month, as_of.day, 12, tzinfo=engine.BJ)
        if args.deceased_year is not None and args.deceased_year > as_of.year:
            raise ValueError("逝世年份不能超过分析年份")
        result = compute(solar_date, hour, minute, args.shichen, args.sex, args.place,
                         args.deceased_year, display, now, engine, args.timezone, args.fold, args.time_basis, args.longitude)
    except ImportError:
        parser.error("缺少依赖，请在虚拟环境安装 requirements.txt")
    except (ValueError, argparse.ArgumentTypeError, OverflowError) as exc:
        parser.error(str(exc))
    warnings = list(result["warnings"])
    if args.timezone is None:
        warnings.append("默认固定北京时间 UTC+08:00；未指定当地时区时不自动处理历史夏令时。")
    if args.sex is None:
        warnings.append("未提供传统顺逆参数；仅输出四柱，不输出大运和依赖该参数的神煞。")
    payload = {
        "schema_version": "1.0", "system": "bazi", "engine": result["engine"],
        "uncertainty": result.get("uncertainty", {"time_known": True, "pillars": {}, "candidates": [], "candidate_limit": 8, "dayun": None}),
        "input": {"solar": result["solar_text"], "lunar": result["lunar_text"], "hour": result["shichen_text"], "sex_convention": result["sex"], "place": result["place"], **{k: result["time"].get(k) for k in ("civil_time", "calendar_time", "fold", "pillar_time")}},
        "conventions": {"timezone": result["time"]["timezone"], "year_boundary": "lichun", "month_boundary": "twelve-jie", "day_boundary": "23:00-next-day", "true_solar_time": args.time_basis == "apparent-solar", "calendar_precision": "lunar-python-1.4.8-full-jieqi", "solar_correction": result["time"].get("solar_correction"), **{k: result["time"][k] for k in ("term_basis", "day_hour_basis", "calendar_timezone")}},
        "pillars": {name: {"gan": cells[0], "zhi": cells[1], "ten_god": cells[2], "hidden_stems": cells[3]} for name, cells in result["pillars"].items()},
        "dayun": result["dayun"],
        "current_year": result["current_year"], "current_ganzhi": result["current_gz"],
        "shensha": [entry for entry in result["shensha_lines"] if args.sex is not None or "元辰" not in entry], "warnings": list(dict.fromkeys(warnings)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
