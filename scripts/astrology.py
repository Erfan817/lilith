#!/usr/bin/env python3
"""Tropical, apparent geocentric longitude data; not a destiny predictor."""
import argparse
from datetime import date, datetime, timedelta, timezone
from importlib.metadata import version
import itertools
import json
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SIGNS = "白羊座 金牛座 双子座 巨蟹座 狮子座 处女座 天秤座 天蝎座 射手座 摩羯座 水瓶座 双鱼座".split()
BODIES = {"Sun": "太阳", "Moon": "月亮", "Mercury": "水星", "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星"}
ASPECTS = (("合相", 0, 8), ("六合", 60, 4), ("刑相", 90, 6), ("拱相", 120, 6), ("对冲", 180, 8))


def parse_datetime(text, zone=None, fold=None, *, allow_upper_endpoint=False):
    if "T" not in text and " " not in text:
        raise ValueError("日期缺出生时刻；不能用午夜代替未知时间")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if zone is not None:
        if dt.tzinfo is not None:
            raise ValueError("明确 UTC 偏移与 --timezone 只能选一个")
        try:
            tz = ZoneInfo(zone)
        except ZoneInfoNotFoundError:
            raise ValueError("IANA 时区不存在；系统无时区数据时请安装 tzdata") from None
        candidates = []
        for candidate_fold in (0, 1):
            localized = dt.replace(tzinfo=tz, fold=candidate_fold)
            utc = localized.astimezone(timezone.utc)
            if utc.astimezone(tz).replace(tzinfo=None) == dt:
                candidates.append((candidate_fold, utc))
        if not candidates:
            raise ValueError("此当地时刻因夏令时跳变而不存在，请核验出生记录")
        if len({utc for _, utc in candidates}) > 1 and fold is None:
            raise ValueError("此时刻因夏令时重复；请指定 --fold 0（第一次）或 --fold 1（第二次）")
        chosen = 0 if fold is None else fold
        dt = next((utc for value, utc in candidates if value == chosen), candidates[0][1])
    elif fold is not None:
        raise ValueError("--fold 只能与 --timezone 同时使用")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("--datetime 必须带明确的 UTC 偏移，如 +08:00 或 Z")
    dt = dt.astimezone(timezone.utc)
    lower = datetime(1900, 1, 1, tzinfo=timezone.utc)
    upper = datetime(2101, 1, 1, tzinfo=timezone.utc)
    if not lower <= dt < upper and not (allow_upper_endpoint and dt == upper):
        raise ValueError("本项目验证范围为 UTC [1900-01-01T00:00:00Z, 2101-01-01T00:00:00Z)")
    return dt


def find_aspects(positions):
    results = []
    for (a, pa), (b, pb) in itertools.combinations(positions.items(), 2):
        separation = abs((pa["longitude"] - pb["longitude"] + 180) % 360 - 180)
        for name, angle, allowed_orb in ASPECTS:
            orb = abs(separation - angle)
            if orb <= allowed_orb:
                results.append({"a": a, "b": b, "name": name, "angle": angle, "separation": separation, "orb": orb, "allowed_orb": allowed_orb})
                break
    return results


def calculate_angles(time, latitude, longitude):
    import astronomy
    phi = math.radians(latitude)
    theta = math.radians((astronomy.SiderealTime(time) * 15 + longitude) % 360)
    zenith = astronomy.Vector(math.cos(phi) * math.cos(theta), math.cos(phi) * math.sin(theta), math.sin(phi), time)
    normal = astronomy.RotateVector(astronomy.Rotation_EQD_ECT(time), zenith)
    if math.hypot(normal.x, normal.y) < 1e-10:
        raise ValueError("当前纬度时刻上升点退化，不能计算宫位")
    asc = math.degrees(math.atan2(normal.x, -normal.y)) % 360
    to_equator = astronomy.Rotation_ECT_EQD(time)
    asc_vector = astronomy.VectorFromSphere(astronomy.Spherical(0, asc, 1), time)
    equator = astronomy.EquatorFromVector(astronomy.RotateVector(to_equator, asc_vector))
    observer = astronomy.Observer(latitude, longitude, 0)
    horizontal = astronomy.Horizon(time, observer, equator.ra, equator.dec, astronomy.Refraction.Airless)
    if horizontal.azimuth >= 180:
        asc = (asc + 180) % 360
    x_axis = astronomy.RotateVector(to_equator, astronomy.Vector(1, 0, 0, time))
    y_axis = astronomy.RotateVector(to_equator, astronomy.Vector(0, 1, 0, time))
    a = -math.sin(theta) * x_axis.x + math.cos(theta) * x_axis.y
    b = -math.sin(theta) * y_axis.x + math.cos(theta) * y_axis.y
    mc = math.atan2(-a, b)
    alignment = math.cos(mc) * (x_axis.x * math.cos(theta) + x_axis.y * math.sin(theta)) + math.sin(mc) * (y_axis.x * math.cos(theta) + y_axis.y * math.sin(theta))
    mc = (math.degrees(mc) + (180 if alignment < 0 else 0)) % 360
    return {"ASC": asc, "DSC": (asc + 180) % 360, "MC": mc, "IC": (mc + 180) % 360}


def chart(text, latitude=None, longitude=None, house_system="whole-sign", zone=None, fold=None):
    import astronomy
    if (latitude is None) != (longitude is None):
        raise ValueError("纬度 --lat 与经度 --lon 必须同时提供")
    if latitude is not None and (not math.isfinite(latitude) or not math.isfinite(longitude) or not -89 < latitude < 89 or not -180 <= longitude <= 180):
        raise ValueError("经纬度必须有限；纬度在 (-89,89)，东经为正且经度在 [-180,180]")
    dt = parse_datetime(text, zone, fold)
    time = astronomy.Time(dt.isoformat().replace("+00:00", "Z"))
    positions = {}
    for name, label in BODIES.items():
        coordinates = astronomy.Ecliptic(astronomy.GeoVector(getattr(astronomy.Body, name), time, True))
        body_longitude = coordinates.elon % 360
        before = astronomy.Ecliptic(astronomy.GeoVector(getattr(astronomy.Body, name), time.AddDays(-0.05), True)).elon
        after = astronomy.Ecliptic(astronomy.GeoVector(getattr(astronomy.Body, name), time.AddDays(0.05), True)).elon
        speed = ((after - before + 180) % 360 - 180) / 0.1
        motion = "near-stationary" if abs(speed) < 0.001 else "retrograde" if speed < 0 else "direct"
        positions[name] = {"name": label, "longitude": body_longitude, "latitude": coordinates.elat, "sign": SIGNS[int(body_longitude // 30)], "sign_degree": body_longitude % 30, "house": None, "longitude_speed_deg_per_day": speed, "motion": motion}
    angles = None if latitude is None else calculate_angles(time, latitude, longitude)
    houses = None
    warnings = ["占星解释仅供文化研究、娱乐与自我反思；天体位置的可计算性不证明命运预测有效。"]
    if angles is not None:
        first = math.floor(angles["ASC"] / 30) * 30 if house_system == "whole-sign" else angles["ASC"]
        houses = {"system": house_system, "cusps": [(first + i * 30) % 360 for i in range(12)]}
        for body in positions.values():
            body["house"] = int(((body["longitude"] - first) % 360) // 30) + 1
        if abs(latitude) >= 66:
            warnings.append("高纬度上升点变化特殊，仅支持整宫/等宫；勿按每两小时一星座推断。")
    else:
        warnings.append("未提供经纬度，未计算上升、天顶与宫位。")
    return {
        "schema_version": "1.0", "datetime_utc": dt.isoformat(),
        "zodiac": "tropical", "frame": "geocentric-apparent-ecliptic-of-date",
        "engine": {"name": "astronomy-engine", "version": version("astronomy-engine")},
        "bodies": positions, "angles": angles, "houses": houses,
        "location": None if latitude is None else {"latitude": latitude, "longitude": longitude},
        "aspects": find_aspects(positions),
        "warnings": warnings,
    }


def date_ranges(text, zone):
    """Sample a known civil day; report uncertainty rather than an invented time."""
    import astronomy
    if not zone:
        raise ValueError("未知出生时刻模式仍需 --timezone 确认民用日期范围")
    day = date.fromisoformat(text)
    start = parse_datetime(day.isoformat() + "T00:00:00", zone)
    end = parse_datetime((day + timedelta(days=1)).isoformat() + "T00:00:00", zone, allow_upper_endpoint=True)
    if end <= start:
        raise ValueError("该民用日期不存在或无法形成有效时间区间")
    samples = [start + (end - start) * index / 96 for index in range(97)]
    ranges = {}
    for name, label in BODIES.items():
        longitudes = [astronomy.Ecliptic(astronomy.GeoVector(getattr(astronomy.Body, name),
                      astronomy.Time(moment.isoformat().replace("+00:00", "Z")), True)).elon % 360
                      for moment in samples]
        base = longitudes[0]
        offsets = [(value - base + 180) % 360 - 180 for value in longitudes]
        ranges[name] = {"name": label, "start_longitude": base, "end_longitude": longitudes[-1],
                        "min_offset_from_start": min(offsets), "max_offset_from_start": max(offsets),
                        "sampled_signs": list(dict.fromkeys(SIGNS[int(value // 30)] for value in longitudes))}
    return {"schema_version": "1.1", "mode": "unknown-time-day-range", "time_known": False,
            "zodiac": "tropical", "frame": "geocentric-apparent-ecliptic-of-date",
            "engine": {"name": "astronomy-engine", "version": version("astronomy-engine")},
            "date_range": {"date": text, "timezone": zone, "start_utc": start.isoformat(),
                           "end_utc": end.isoformat(), "end_exclusive": True},
            "range_method": "97-point sampled day including endpoint for bounds; not a solved ingress search",
            "body_ranges": ranges, "bodies": None, "angles": None, "houses": None, "aspects": None,
            "location": None,
            "warnings": ["出生时刻未知：只给当日抽样范围；不把任何样本当成本命时刻。",
                         "端点只用于范围包络；换座和停滞附近需精确搜索，抽样不是完整误差证明。",
                         "不输出上升、宫位、精确月亮位置或相位；天体坐标不证明占星预测有效。"]}


def main():
    parser = argparse.ArgumentParser(description="西方占星天文数据（热带黄道，十天体）")
    times = parser.add_mutually_exclusive_group(required=True)
    times.add_argument("--datetime", help="带 UTC 偏移的公历 ISO 日期时间")
    times.add_argument("--date", help="仅知公历日期 YYYY-MM-DD；需 --timezone，输出抽样范围")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--houses", choices=("whole-sign", "equal"), default="whole-sign")
    parser.add_argument("--timezone", help="IANA 时区，如 Asia/Shanghai；不能与 UTC 偏移同时给")
    parser.add_argument("--fold", choices=(0, 1), type=int, help="夏令时重复时间第0/1次")
    args = parser.parse_args()
    try:
        if args.date:
            if args.lat is not None or args.lon is not None or args.fold is not None:
                raise ValueError("未知时刻模式不接受经纬度或 --fold，不能借此计算四轴")
            result = date_ranges(args.date, args.timezone)
        else:
            result = chart(args.datetime, args.lat, args.lon, args.houses, args.timezone, args.fold)
    except ImportError:
        parser.error("缺少依赖，请在虚拟环境安装 requirements.txt")
    except (ValueError, OverflowError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
