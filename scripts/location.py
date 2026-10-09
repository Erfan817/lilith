#!/usr/bin/env python3
"""Opt-in city-only Nominatim lookup; never send birth data or infer timezones."""
import argparse
import json
import math
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def parse_candidates(rows):
    if not isinstance(rows, list):
        raise ValueError("地图服务没有返回候选列表")
    candidates = []
    for row in rows[:3]:
        if (not isinstance(row, dict) or not isinstance(row.get("display_name"), str)
                or not row["display_name"].strip() or len(row["display_name"]) > 2000
                or any(0xD800 <= ord(c) <= 0xDFFF for c in row["display_name"])):
            raise ValueError("地图候选名称缺失或含无效Unicode")
        if any(type(row.get(key)) not in (str, int, float) for key in ("lat", "lon")):
            raise ValueError("地图坐标必须是数字或数字字符串，不能是布尔值")
        osm_type, osm_id = row.get("osm_type"), row.get("osm_id")
        if osm_type is not None and osm_type not in ("node", "way", "relation"):
            raise ValueError("地图对象类型无效")
        if osm_id is not None and (type(osm_id) is not int or not 0 <= osm_id < 2**63):
            raise ValueError("地图对象编号无效")
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("地图候选坐标缺失或无效") from exc
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError("地图候选坐标无效")
        candidates.append({"name": row["display_name"], "latitude": lat, "longitude": lon,
                           "osm_type": row.get("osm_type"), "osm_id": row.get("osm_id"), "timezone": None})
    return candidates


def main():
    parser = argparse.ArgumentParser(description="城市坐标候选查询；显式允许联网，不发送生日、不猜时区")
    parser.add_argument("--query-file", required=True, help="只含城市和国家的 UTF-8 文件")
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    payload = {"schema_version": "1.0", "network_used": False, "timezone": None, "candidates": [],
               "requires_confirmation": True, "source": "OpenStreetMap/Nominatim", "success": False}
    if not args.allow_network:
        payload.update(error_type="network_permission_required", error="先征得允许，只把城市/国家查询发送给地图服务；也可直接提供已确认坐标和时区。")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    try:
        with Path(args.query_file).open("rb") as source:
            raw = source.read(1025)
        if len(raw) > 1024:
            raise ValueError("城市查询文件不能超过1024字节")
        query = raw.decode("utf-8").strip()
        if not query or len(query) > 200 or any(ord(c) < 32 for c in query):
            raise ValueError("查询只接受单行城市/国家名，最多200字符")
        # A single fixed-origin request; no server loop, guessing or automatic retry.
        url = "https://nominatim.openstreetmap.org/search?" + urlencode({"q": query, "format": "jsonv2", "limit": 3})
        request = Request(url, headers={"User-Agent": "Lilith-Diviner/0.2 (https://github.com/Erfan817/lilith-diviner)", "Accept": "application/json"})
        payload["network_used"] = True
        with urlopen(request, timeout=15) as response:
            body = response.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise ValueError("地图响应过大")
        payload["candidates"] = parse_candidates(json.loads(body.decode("utf-8")))
        payload["success"] = True
        payload["attribution"] = "© OpenStreetMap contributors; Nominatim geocoding"
        payload["guidance"] = "候选需用户确认；时区仍需独立确认。请勿用此命令批量查询，遵守Nominatim每秒最多一请求和服务政策。"
    except (OSError, URLError, TimeoutError) as exc:
        payload.update(error_type="lookup_failed", error="城市服务连接或文件读取失败；请先告知用户并改用已核验的坐标/IANA时区。")
    except (ValueError, UnicodeError) as exc:
        payload.update(error_type="invalid_data", error=str(exc))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["success"] else 2


if __name__ == "__main__":
    sys.exit(main())
