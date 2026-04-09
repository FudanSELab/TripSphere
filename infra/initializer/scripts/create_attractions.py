#!/usr/bin/env -S uv run --script
"""
Attraction Data Creation Script

Reads raw attraction data from attractions.csv, matches each attraction to a POI in
the seeded pois.json (by name), and produces attractions.json conforming to the
AttractionDoc structure expected by trip-attraction-service.

Field mapping:
  - name           → name
  - type           → tags  (split by '/')
  - lat/lon        → NOT used; coordinates come from matched POI
  - opentime/endtime → openingHours.rules (one rule covering all 7 days)
  - price          → ticketInfo.estimatedPrice  (CNY)
  - recommendmintime/recommendmaxtime → recommendTime
  - temporarilyClosed → always false
  - introduction/images → null / []

Output structure (per document):
{
    "_id":              str  (UUID7),
    "name":             str,
    "poiId":            str | null,
    "location":         {"type": "Point", "coordinates": [lng, lat]},
    "address":          {"province": str, "city": str, "district": str, "detailed": str},
    "introduction":     null,
    "tags":             [str],
    "images":           [],
    "openingHours":     {
        "rules": [{
            "days": ["MONDAY", ..., "SUNDAY"],
            "timeRanges": [{"openTime": "HH:MM:SS", "closeTime": "HH:MM:SS", "lastEntryTime": null}],
            "note": null
        }],
        "specialTips": null
    },
    "temporarilyClosed": false,
    "ticketInfo":       {"estimatedPrice": {"currency": "CNY", "amount": number}, "metadata": null},
    "recommendTime":    {"minHours": float, "maxHours": float},
    "createdAt":        str (ISO-8601 UTC),
    "updatedAt":        str (ISO-8601 UTC),
}
"""  # noqa: E501

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
SEEDED_DIR = DATA_DIR / "seeded"

INPUT_CSV = DATA_DIR / "database" / "attractions" / "shanghai" / "attractions.csv"
SEEDED_POIS_FILE = SEEDED_DIR / "shanghai" / "pois.json"
OUTPUT_FILE = SEEDED_DIR / "shanghai" / "attractions.json"
UNMATCHED_FILE = TEMP_DIR / "unmatched_attractions.json"

# ---------------------------------------------------------------------------
# UUID7 helper (reuse from the shared utils package when available, otherwise
# fall back to uuid4 so the script works standalone too)
# ---------------------------------------------------------------------------
try:
    sys.path.insert(0, str(BASE_DIR / "src"))
    from initializer.utils.uuid import uuid7 as _uuid7

    def generate_id() -> str:
        return str(_uuid7())

except ImportError:
    import uuid

    def generate_id() -> str:  # type: ignore[misc]
        return str(uuid.uuid4())


def normalize_name(name: str) -> str:
    """Normalise a name for comparison."""
    name = name.strip()
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("【", "[").replace("】", "]")
    name = name.replace("・", "·")
    return name


def extract_core_name(name: str) -> str:
    """Strip bracketed suffixes, e.g. 「星巴克(南京路店)」→「星巴克」."""
    core = re.sub(r"\([^)]*\)", "", name)
    core = re.sub(r"\[[^\]]*\]", "", core)
    return core.strip()


def similarity(name1: str, name2: str) -> float:
    """Return a similarity score in [0, 1] between two names."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if n1 == n2:
        return 1.0

    c1 = extract_core_name(n1)
    c2 = extract_core_name(n2)
    if c1 == c2 and c1:
        return 0.95

    if n1 in n2:
        r = len(n1) / len(n2)
        if r >= 0.7:
            return 0.8 * r
    elif n2 in n1:
        r = len(n2) / len(n1)
        if r >= 0.7:
            return 0.8 * r

    if c1 and c2:
        if c1 in c2:
            r = len(c1) / len(c2)
            if r >= 0.6:
                return 0.7 * r
        elif c2 in c1:
            r = len(c2) / len(c1)
            if r >= 0.6:
                return 0.7 * r

    return 0.0


# ---------------------------------------------------------------------------
# POI index
# ---------------------------------------------------------------------------


def build_poi_index(
    pois: list[dict],
) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """
    Build two lookup structures over the seeded POI list.

    Returns:
        exact_index  – normalised_name → poi
        core_index   – core_name       → [poi, ...]
    """
    exact: dict[str, dict] = {}
    core: dict[str, list[dict]] = {}

    for poi in pois:
        name = poi.get("name", "").strip()
        if not name:
            continue
        norm = normalize_name(name)
        c = extract_core_name(norm)

        if norm not in exact:
            exact[norm] = poi

        if c:
            core.setdefault(c, []).append(poi)

    return exact, core


def find_poi(
    attraction_name: str,
    exact_index: dict[str, dict],
    core_index: dict[str, list[dict]],
) -> dict | None:
    """Look up the best matching POI for *attraction_name*."""
    norm = normalize_name(attraction_name)
    core = extract_core_name(norm)

    # 1. Exact match
    if norm in exact_index:
        return exact_index[norm]

    # 2. Core name exact match
    if core in core_index:
        candidates = core_index[core]
        if len(candidates) == 1:
            return candidates[0]
        best, best_score = None, 0.0
        for c in candidates:
            s = similarity(attraction_name, c.get("name", ""))
            if s > best_score:
                best_score, best = s, c
        if best_score >= 0.7:
            return best

    # 3. Full scan for high-similarity matches
    best, best_score = None, 0.0
    for key, poi in exact_index.items():
        s = similarity(attraction_name, key)
        if s > best_score:
            best_score, best = s, poi
    if best_score >= 0.8:
        return best

    return None


# All days of week in Java DayOfWeek enum order (Monday first)
ALL_DAYS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_tags(type_raw: str) -> list[str]:
    """Split type field by '/' into a list of tags."""
    if not type_raw or not type_raw.strip():
        return []
    return [t.strip() for t in type_raw.split("/") if t.strip()]


def parse_time_str(time_str: str) -> str | None:
    """
    Parse a time string like "09:00" or "24:00" into "HH:MM:SS" format
    suitable for Java LocalTime serialisation.

    Returns None if the input is empty or unparseable.
    Special case: "24:00" → "23:59:59" (end-of-day representation).
    """
    if not time_str or not time_str.strip():
        return None
    try:
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if hour == 24:
            # Map 24:00 (= midnight next day) to last representable second
            return "23:59:59"
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}:00"
    except (ValueError, IndexError):
        pass
    return None


def build_opening_hours(opentime_raw: str, endtime_raw: str) -> dict | None:
    """
    Build the openingHours sub-document from raw CSV strings.

    Returns None when the times are invalid or openTime >= closeTime
    (which would violate the TimeRange invariant in OpenRule.java).
    """
    open_time = parse_time_str(opentime_raw)
    close_time = parse_time_str(endtime_raw)

    if not open_time or not close_time:
        return None

    # openTime must be strictly before closeTime
    if open_time >= close_time:
        return None

    return {
        "rules": [
            {
                "days": ALL_DAYS,
                "timeRanges": [
                    {
                        "openTime": open_time,
                        "closeTime": close_time,
                        "lastEntryTime": None,
                    }
                ],
                "note": None,
            }
        ],
        "specialTips": None,
    }


def build_ticket_info(price_raw: str) -> dict | None:
    """
    Build the ticketInfo sub-document from the raw price string.

    Returns None when the price cell is empty or unparseable.
    A price of 0 is valid (free admission).
    """
    if not price_raw or not price_raw.strip():
        return None
    try:
        amount = float(price_raw.strip())
        return {
            "estimatedPrice": {
                "currency": "CNY",
                "amount": amount,
            },
            "metadata": None,
        }
    except ValueError:
        return None


def build_recommend_time(min_raw: str, max_raw: str) -> dict | None:
    """
    Build the recommendTime sub-document.

    Returns None when either value is missing, non-positive, or when
    maxHours <= minHours (which would violate the RecommendTime record
    invariant in RecommendTime.java).
    """
    try:
        min_hours = float(min_raw.strip()) if min_raw and min_raw.strip() else None
        max_hours = float(max_raw.strip()) if max_raw and max_raw.strip() else None
        if min_hours is not None and max_hours is not None:
            if min_hours > 0 and max_hours > min_hours:
                return {"minHours": min_hours, "maxHours": max_hours}
    except ValueError:
        pass
    return None


def build_attraction_doc(
    row: dict,
    poi: dict | None,
    fallback_lat: float,
    fallback_lon: float,
) -> dict:
    """Construct a single AttractionDoc-compatible JSON document."""
    ts = now_iso()

    # --- location & address ---
    if poi is not None:
        location = poi.get("location", {})
        address = poi.get(
            "address",
            {"province": "", "city": "", "district": "", "detailed": ""},
        )
        poi_id = poi.get("_id")
    else:
        # Fallback: use CSV coordinates (GeoJSON is [lng, lat])
        location = {
            "type": "Point",
            "coordinates": [fallback_lon, fallback_lat],
        }
        address = {"province": "", "city": "", "district": "", "detailed": ""}
        poi_id = None

    doc = {
        "_id": generate_id(),
        "name": row.get("name", "").strip(),
        "poiId": poi_id,
        "location": location,
        "address": address,
        "introduction": None,
        "tags": parse_tags(row.get("type", "")),
        "images": [],
        "openingHours": build_opening_hours(
            row.get("opentime", ""), row.get("endtime", "")
        ),
        "temporarilyClosed": False,
        "ticketInfo": build_ticket_info(row.get("price", "")),
        "recommendTime": build_recommend_time(
            row.get("recommendmintime", ""), row.get("recommendmaxtime", "")
        ),
        "createdAt": ts,
        "updatedAt": ts,
    }
    return doc


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"已保存: {path}")


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("景点数据转换脚本 (CSV → AttractionDoc JSON)")
    print("=" * 60)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load inputs
    print(f"\n加载CSV: {INPUT_CSV}")
    attractions_csv = load_csv(INPUT_CSV)
    print(f"共 {len(attractions_csv)} 条景点记录")

    print(f"\n加载已种子化POI数据: {SEEDED_POIS_FILE}")
    seeded_pois: list[dict] = load_json(SEEDED_POIS_FILE)  # type: ignore[assignment]
    print(f"共 {len(seeded_pois)} 个POI")

    # 2. Build POI index
    print("\n构建POI索引...")
    exact_index, core_index = build_poi_index(seeded_pois)
    print(f"精确索引: {len(exact_index)} 条目  核心索引: {len(core_index)} 条目")

    # 3. Convert each attraction row
    print("\n开始转换景点数据...")
    print("-" * 40)

    attraction_docs: list[dict] = []
    unmatched: list[dict] = []
    matched_count = 0

    total = len(attractions_csv)
    for i, row in enumerate(attractions_csv, 1):
        name = row.get("name", "").strip()

        try:
            fallback_lat = float(row.get("lat", 0) or 0)
            fallback_lon = float(row.get("lon", 0) or 0)
        except ValueError:
            fallback_lat, fallback_lon = 0.0, 0.0

        poi = find_poi(name, exact_index, core_index)

        if poi:
            matched_name = poi.get("name", "")
            tag = (
                "✓ 精确匹配"
                if normalize_name(matched_name) == normalize_name(name)
                else f"✓ 匹配到: {matched_name}"
            )
            matched_count += 1
        else:
            tag = "✗ 未匹配，使用CSV坐标"
            unmatched.append({"name": name, "row": row})

        print(f"[{i:>3}/{total}] {name}  →  {tag}")

        doc = build_attraction_doc(row, poi, fallback_lat, fallback_lon)
        attraction_docs.append(doc)

    # 4. Save outputs
    print("\n" + "-" * 40)
    save_json(attraction_docs, OUTPUT_FILE)

    if unmatched:
        save_json(unmatched, UNMATCHED_FILE)

    # 5. Summary
    print("\n" + "=" * 60)
    print("转换完成!")
    print(f"  总记录数   : {total}")
    print(f"  成功匹配POI: {matched_count}")
    print(f"  未匹配     : {len(unmatched)}")
    print(f"  输出文件   : {OUTPUT_FILE}")
    if unmatched:
        print(f"  未匹配记录 : {UNMATCHED_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
