"""Full lunar-python BaZi calculations; vendor is used for rule tables only."""
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import Solar
from lunar_python.util import LunarUtil

BJ = timezone(timedelta(hours=8))
EIGHT_CHAR_SECT = 1  # 23:00 advances the day, unlike EightChar's default sect=2.
NAMES = ("year", "month", "day", "hour")


def solar_of(dt):
    """Feed a wall-clock date/time to the library's timezone-free Solar API."""
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def datetime_of(solar):
    """The library's ephemeris Solar times are fixed Beijing, not local IANA."""
    return datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                    solar.getHour(), solar.getMinute(), solar.getSecond(), tzinfo=BJ)


def get_zone(name):
    if name is None:
        return BJ
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("--timezone 需要有效 IANA 时区名称") from exc


def resolve_civil(naive, zone, fold=None):
    """Round-trip both folds via UTC; reject imaginary/ambiguous wall clocks."""
    valid = {}
    for choice in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=choice)
        back = aware.astimezone(timezone.utc).astimezone(zone)
        if back.replace(tzinfo=None) == naive:
            valid[choice] = aware
    instants = {v.astimezone(timezone.utc) for v in valid.values()}
    if not instants:
        raise ValueError("当地民用时刻不存在（时区/DST 跳时缺口），请核对出生记录")
    if len(instants) > 1 and fold is None:
        raise ValueError("当地民用时刻有歧义（时区/DST 回拨），请指定 --fold 0 或 1")
    return valid[fold if fold is not None else min(valid)]


def eight_char_of(clock):
    ec = solar_of(clock).getLunar().getEightChar()
    ec.setSect(EIGHT_CHAR_SECT)
    return ec


def pillar_cells(eight_char, name, unknown=False, day_gan=None):
    if unknown:
        return ("未知",) * 4
    prefix = {"year": "Year", "month": "Month", "day": "Day", "hour": "Time"}[name]
    gan = getattr(eight_char, "get" + prefix + "Gan")()
    zhi = getattr(eight_char, "get" + prefix + "Zhi")()
    ten_god = "—" if name == "day" else LunarUtil.SHI_SHEN[(day_gan or eight_char.getDayGan()) + gan]
    hidden = getattr(eight_char, "get" + prefix + "HideGan")()
    return gan, zhi, ten_god, "、".join(g + LunarUtil.WU_XING_GAN[g] for g in hidden)


def engine_metadata():
    return {"name": "lunar-python", "version": version("lunar-python"),
            "eight_char_sect": EIGHT_CHAR_SECT, "yun_sect": 2, "official_almanac": False}


def time_metadata(zone_name, civil=None, calendar=None, fold=None):
    return {"timezone": zone_name or "UTC+08:00", "fold": fold,
            "civil_time": civil.isoformat() if civil else None,
            "calendar_time": calendar.isoformat() if calendar else None,
            "term_basis": "absolute-instant", "day_hour_basis": "local-civil",
            "calendar_timezone": "UTC+08:00"}


def civil_domains(solar_date, shichen):
    """A branch is a two-hour range, not a claimed midpoint birth time."""
    midnight = datetime(solar_date.year, solar_date.month, solar_date.day)
    if shichen is None:
        hours = [(0, 24)]
    elif shichen == "子":
        hours = [(0, 1), (23, 24)]
    else:
        left = (LunarUtil.ZHI.index(shichen) - 1) * 2 - 1
        hours = [(left, left + 2)]
    return [(midnight + timedelta(hours=a), midnight + timedelta(hours=b)) for a, b in hours]


def real_domains(solar_date, shichen, zone):
    """Intersect civil ranges with constant-offset UTC segments, including folds.

    Hourly bracketing plus second-resolution bisection detects IANA offset
    transitions; there are no multiple transitions within an hour in the
    supported 1900-2100 IANA data. Work is bounded to a three-day window.
    """
    domains = civil_domains(solar_date, shichen)
    midnight = datetime(solar_date.year, solar_date.month, solar_date.day, tzinfo=timezone.utc)
    start, end = midnight - timedelta(hours=26), midnight + timedelta(hours=50)
    boundaries = [start]
    cursor = start
    offset = cursor.astimezone(zone).utcoffset()
    while cursor < end:
        probe = min(cursor + timedelta(hours=1), end)
        new_offset = probe.astimezone(zone).utcoffset()
        if new_offset != offset:
            lo, hi = cursor, probe
            while (hi - lo).total_seconds() > 1:
                mid = lo + timedelta(seconds=int((hi - lo).total_seconds() / 2))
                if mid.astimezone(zone).utcoffset() == offset:
                    lo = mid
                else:
                    hi = mid
            boundaries.append(hi)
            offset = new_offset
        cursor = probe
    boundaries.append(end)
    result = []
    for a, b in zip(boundaries, boundaries[1:]):
        offset = a.astimezone(zone).utcoffset()
        for left, right in domains:
            lo = max(a, (left - offset).replace(tzinfo=timezone.utc))
            hi = min(b, (right - offset).replace(tzinfo=timezone.utc))
            if lo < hi:
                result.append((lo, hi, offset))
    if not result:
        raise ValueError("出生日期/时辰在当地时区不存在（跳日或 DST 缺口），请核对出生记录")
    return sorted(result)


def jie_instants(calendar_dt):
    lunar = solar_of(calendar_dt).getLunar()
    table = lunar.getJieQiTable()
    return [datetime_of(table[lunar.JIE_QI_IN_USE[i]])
            for i in range(0, len(lunar.JIE_QI_IN_USE), 2)]


def unknown_clock(solar_date, shichen, sex, place, deceased_year, lunar_display, now,
                  zone_name=None):
    """Partition the entire real domain; output only invariant cells and candidates."""
    zone = get_zone(zone_name)
    domains = real_domains(solar_date, shichen, zone)
    calendar_lower = datetime(1900, 1, 1, tzinfo=BJ)
    calendar_upper = datetime(2101, 1, 1, tzinfo=BJ)
    if any(left < calendar_lower or right > calendar_upper for left, right, _ in domains):
        raise ValueError("未知时间域换算后超出1900–2100范围；请确认更具体钟点，不截断候选")
    candidates, cells = [], []
    day_boundary = datetime(solar_date.year, solar_date.month, solar_date.day, 23)
    for left, right, offset in domains:
        cuts = {left, right}
        boundary = (day_boundary - offset).replace(tzinfo=timezone.utc)
        if left < boundary < right:
            cuts.add(boundary)
        for event in jie_instants(left.astimezone(BJ)):
            if left < event < right:
                cuts.add(event.astimezone(timezone.utc))
        cuts = sorted(cuts)
        for a, b in zip(cuts, cuts[1:]):
            local = a.astimezone(zone)
            calendar_ec = eight_char_of(a.astimezone(BJ))
            local_ec = eight_char_of(local)
            detail = {n: pillar_cells(calendar_ec if n in ("year", "month") else local_ec,
                                      n, n == "hour" and shichen is None,
                                      day_gan=local_ec.getDayGan()) for n in NAMES}
            cells.append(detail)
            candidates.append({"interval": {"start": local.isoformat(),
                                            "end_exclusive": b.astimezone(zone).isoformat()},
                               "pillars": {"year": calendar_ec.getYear(), "month": calendar_ec.getMonth(),
                                           "day": local_ec.getDay(),
                                           "hour": local_ec.getTime() if shichen else None}})
    if len(candidates) > 8:
        raise ValueError("时间不确定区间超过候选上限，请提供更具体出生时刻")
    possibilities = {n: list(dict.fromkeys(c["pillars"][n] for c in candidates
                                          if c["pillars"][n] is not None)) for n in NAMES}
    merged = {n: tuple(values[0] if len(set(values)) == 1 else "未知"
                       for values in zip(*(c[n] for c in cells))) for n in NAMES}
    current_year = deceased_year if deceased_year is not None else now.year
    warnings = ["未知出生时间或仅知时辰；仅输出稳定字段与受限候选，不以正午或时辰中点代替真实出生时刻。",
                "起运需要具体钟点，dayun 保持 null；不输出未经唯一日干核验的神煞。"]
    if shichen == "子":
        warnings.append("子时包含当日早子及当日晚子，保留23点换日的两个候选。")
    return {"solar_text": solar_date.isoformat(), "lunar_text": lunar_display,
            "shichen_text": shichen or "未知", "sex": sex, "place": place,
            "pillars": merged, "dayun": None, "shensha_lines": [],
            "current_year": current_year,
            "current_gz": LunarUtil.JIA_ZI[(current_year - 4) % 60], "hour_unknown": shichen is None,
            "warnings": warnings, "engine": engine_metadata(), "time": time_metadata(zone_name),
            "uncertainty": {"time_known": False, "pillars": possibilities,
                            "candidates": candidates, "candidate_limit": 8,
                            "dayun": "clock-time-required"}}


def apparent_solar_clock(civil, longitude):
    """Derive local apparent solar clock from solar RA and sidereal rotation.

    This is a clock label for day/hour rules, not a new physical instant.
    Calendar terms and fortune-cycle durations still use the original instant.
    """
    import astronomy
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("太阳时经度需为 [-180,180] 的有限数值；东经为正")
    utc = civil.astimezone(timezone.utc)
    instant = astronomy.Time(utc.isoformat().replace("+00:00", "Z"))
    vector = astronomy.RotateVector(astronomy.Rotation_EQJ_EQD(instant),
                                    astronomy.GeoVector(astronomy.Body.Sun, instant, True))
    sun = astronomy.EquatorFromVector(vector)
    apparent_greenwich = ((astronomy.SiderealTime(instant) * 15 - sun.ra * 15 + 180) % 360) * 4
    mean_greenwich = utc.hour * 60 + utc.minute + utc.second / 60 + utc.microsecond / 60000000
    equation = (apparent_greenwich - mean_greenwich + 720) % 1440 - 720
    correction = equation + 4 * longitude - civil.utcoffset().total_seconds() / 60
    label = civil.replace(tzinfo=None) + timedelta(minutes=correction)
    metadata = {"longitude_degrees_east": longitude, "equation_of_time_minutes": equation,
                "correction_minutes": correction, "engine": "astronomy-engine",
                "engine_version": version("astronomy-engine"), "pillar_clock_is_instant": False,
                "method": "apparent solar RA of date and sidereal rotation; UTC approximates UT1"}
    return label, metadata


def compute(solar_date, hour, minute, shichen, sex, place, deceased_year,
            lunar_display, now, rules, zone_name=None, fold=None, time_basis="civil", longitude=None):
    """Year/month/Yun use the instant; day/hour use the declared local clock."""
    zone = get_zone(zone_name)
    if fold is not None and (zone_name is None or hour is None):
        raise ValueError("--fold 仅用于明确 IANA 时区和钟点的回拨歧义")
    if time_basis != "civil" and (time_basis != "apparent-solar" or hour is None or longitude is None):
        raise ValueError("太阳时模式需已确认钟点和 --longitude，不接受未知时刻或只有时辰")
    if time_basis == "civil" and longitude is not None:
        raise ValueError("--longitude 需配 --time-basis apparent-solar，不能静默校正时间")
    if hour is None:
        return unknown_clock(solar_date, shichen, sex, place, deceased_year,
                             lunar_display, now, zone_name)
    civil = resolve_civil(datetime(solar_date.year, solar_date.month, solar_date.day,
                                   hour, minute), zone, fold)
    birth_dt = civil.astimezone(BJ)
    lunar = solar_of(birth_dt).getLunar()
    calendar_ec = eight_char_of(birth_dt)
    clock, correction = apparent_solar_clock(civil, longitude) if time_basis == "apparent-solar" else (civil, None)
    if not 1900 <= clock.year <= 2100 or not 1900 <= birth_dt.year <= 2100:
        raise ValueError("时区/太阳时换算后超出1900–2100范围")
    local_ec = eight_char_of(clock)
    pillars = {n: pillar_cells(calendar_ec if n in ("year", "month") else local_ec,
                              n, day_gan=local_ec.getDayGan()) for n in NAMES}
    shichen = local_ec.getTimeZhi()
    warnings = ["节气与四柱采用 lunar-python 1.4.8 完整接口；库结果并非官方历书认证。"]
    dayun = None
    if sex is not None:
        yun = calendar_ec.getYun(1 if sex == "男" else 0, 2)
        periods = [{"index": d.getIndex(), "ganzhi": d.getGanZhi(),
                    "start_year": d.getStartYear(), "end_year": d.getEndYear(),
                    "start_age": d.getStartAge(), "end_age": d.getEndAge()}
                   for d in yun.getDaYun(9)]
        rows = [[str(d["index"]), "%d-%d岁" % (d["start_age"], d["end_age"]),
                 d["ganzhi"]] for d in periods if d["index"] > 0]
        dayun = {"direction": "forward" if yun.isForward() else "reverse",
                 "start_age": {"years": yun.getStartYear(), "months": yun.getStartMonth(),
                               "days": yun.getStartDay(), "hours": yun.getStartHour()},
                 "start_solar": datetime_of(yun.getStartSolar()).isoformat(),
                 "start_solar_timezone": "UTC+08:00",
                 "rows": rows, "periods": periods,
                 "period_age_convention": "nominal-year-age"}
    for jie in (lunar.getPrevJie(), lunar.getNextJie()):
        if abs((datetime_of(jie.getSolar()) - birth_dt).total_seconds()) <= 86400:
            warnings.append("节气交界；输入钟点或时区误差可能改变年/月柱。")
    if place:
        warnings.append("--place 仅展示，不自动查找时区或经度。")
    shensha = rules.compute_shensha(*(v for n in NAMES for v in pillars[n][:2]), sex)
    current_year = deceased_year if deceased_year is not None else now.year
    time = time_metadata(zone_name, civil, birth_dt, fold)
    time.update(pillar_time=clock.isoformat(), day_hour_basis="local-apparent-solar" if correction else "local-civil",
                solar_correction=correction)
    if correction:
        warnings.append("已显式采用地方视太阳钟标计算日/时柱；交节与起运仍用原绝对时刻，太阳钟标不是新出生瞬间。")
    return {
        "solar_text": solar_date.isoformat() + " %02d:%02d" % (hour, minute),
        "lunar_text": lunar_display, "shichen_text": "%s / %02d:%02d" % (shichen, hour, minute),
        "sex": sex, "place": place, "pillars": pillars, "dayun": dayun,
        "current_year": current_year, "current_gz": LunarUtil.JIA_ZI[(current_year - 4) % 60],
        "warnings": warnings, "hour_unknown": False, "shensha_lines": shensha,
        "engine": engine_metadata(), "time": time,
    }
