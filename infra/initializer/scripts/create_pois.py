#!/usr/bin/env -S uv run --script
"""
POI Data Creation Script

Starting from original POI data (poi.json), uses pre-scraped Amap data (amap_pois.json)
or Amap API to enrich POI information and generate complete POI data conforming to
PoiDoc structure.

Output structure:
{
    "_id": str (UUID7),
    "name": str,
    "location": {"type": "Point", "coordinates": [lng, lat]},
    "address": {"province": str, "city": str, "district": str, "detailed": str},
    "adcode": str,
    "amapId": str,
    "categories": [str],
    "images": [str],
    "createdAt": str (ISO-8601 UTC),
    "updatedAt": str (ISO-8601 UTC)
}
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from initializer.utils.uuid import uuid7

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
SEEDED_DIR = DATA_DIR / "seeded"

# Input/output files
ORIGINAL_POI_FILE = DATA_DIR / "database" / "poi" / "shanghai" / "poi.json"
AMAP_POIS_FILE = DATA_DIR / "amap_pois.json"
OUTPUT_FILE = SEEDED_DIR / "shanghai" / "pois.json"

# Intermediate result files
UNMATCHED_FILE = TEMP_DIR / "unmatched_pois.json"
API_RESULTS_FILE = TEMP_DIR / "api_results.json"


def load_env():
    """Load environment variables"""
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path)
    amap_key = os.getenv("AMAP_KEY") or os.getenv("AMAP_API_KEY")
    if not amap_key:
        print(f"警告: 未找到AMAP_KEY环境变量，请检查 {env_path}")
    return amap_key


def load_json(file_path: Path) -> list | dict:
    """Load JSON file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Path):
    """Save JSON file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"已保存: {file_path}")


def normalize_name(name: str) -> str:
    """
    Normalize POI name for matching
    Unify brackets, remove whitespace characters
    """
    name = name.strip()
    # Unify bracket types
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("【", "[").replace("】", "]")
    # Unify Chinese punctuation
    name = name.replace("·", "·").replace("・", "·")
    return name


def extract_core_name(name: str) -> str:
    """
    Extract core name (remove store information in brackets)
    Example: "星巴克(南京路店)" -> "星巴克"
    """
    # Remove brackets and their contents
    core = re.sub(r"\([^)]*\)", "", name)
    core = re.sub(r"\[[^\]]*\]", "", core)
    return core.strip()


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names (0-1)
    Uses multiple strategies for comprehensive scoring
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # 1. Exact match
    if n1 == n2:
        return 1.0

    # 2. Core name match
    core1 = extract_core_name(n1)
    core2 = extract_core_name(n2)
    if core1 == core2 and core1:
        return 0.95

    # 3. One contains the other (consider length ratio)
    if n1 in n2:
        ratio = len(n1) / len(n2)
        # Short name must account for at least 70% of long name to be considered a match
        if ratio >= 0.7:
            return 0.8 * ratio
    elif n2 in n1:
        ratio = len(n2) / len(n1)
        if ratio >= 0.7:
            return 0.8 * ratio

    # 4. Core name containment relationship
    if core1 and core2:
        if core1 in core2:
            ratio = len(core1) / len(core2)
            if ratio >= 0.6:
                return 0.7 * ratio
        elif core2 in core1:
            ratio = len(core2) / len(core1)
            if ratio >= 0.6:
                return 0.7 * ratio

    return 0.0


def build_amap_index(
    amap_pois: list[dict],
) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """
    Build Amap POI index
    Returns:
        - exact_index: {normalized_name: poi_data} Exact match index
        - core_index: {core_name: [poi_data, ...]} Core name index (for fuzzy matching)
    """
    exact_index = {}
    core_index = {}

    for poi in amap_pois:
        name = poi.get("name", "").strip()
        if not name:
            continue

        normalized = normalize_name(name)
        core = extract_core_name(normalized)

        # Exact index (keep only the first one)
        if normalized not in exact_index:
            exact_index[normalized] = poi

        # Core name index (allow multiple)
        if core:
            if core not in core_index:
                core_index[core] = []
            core_index[core].append(poi)

    return exact_index, core_index


def find_in_amap_data(
    poi_name: str, exact_index: dict[str, dict], core_index: dict[str, list[dict]]
) -> dict | None:
    """
    Find matching POI in pre-scraped Amap data
    Uses multi-layer matching strategy to ensure accuracy
    """
    normalized = normalize_name(poi_name)
    core = extract_core_name(normalized)

    # 1. Exact match (highest priority)
    if normalized in exact_index:
        return exact_index[normalized]

    # 2. Core name exact match
    if core in core_index:
        candidates = core_index[core]
        # If there's only one candidate, return it directly
        if len(candidates) == 1:
            return candidates[0]
        # When there are multiple candidates, choose the most similar one
        best_match = None
        best_score = 0.0
        for candidate in candidates:
            score = calculate_similarity(poi_name, candidate.get("name", ""))
            if score > best_score:
                best_score = score
                best_match = candidate
        if best_score >= 0.7:
            return best_match

    # 3. Traverse exact index to find high similarity matches
    best_match = None
    best_score = 0.0
    for key, poi in exact_index.items():
        score = calculate_similarity(poi_name, key)
        if score > best_score:
            best_score = score
            best_match = poi

    # Only return if similarity is high enough
    if best_score >= 0.8:
        return best_match

    return None


def search_amap_api(poi_name: str, api_key: str, region: str = "上海市") -> dict | None:
    """
    Query POI information using Amap search API
    API: https://restapi.amap.com/v5/place/text

    Returns the first search result (prioritizing exact matches)
    """
    if not api_key:
        print(f"  跳过API搜索 (无API Key): {poi_name}")
        return None

    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": api_key,
        "keywords": poi_name,
        "region": region,
        "show_fields": "business,photos,children,navi",
    }

    try:
        print(f"  调用API搜索: {poi_name}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "1" and data.get("pois"):
            pois = data["pois"]
            # Prioritize returning exactly matched names
            for poi in pois:
                if normalize_name(poi.get("name", "")) == normalize_name(poi_name):
                    return poi
            # Otherwise return the first result
            return pois[0]
        else:
            print(f"  API未找到结果: {poi_name}")
            return None
    except requests.RequestException as e:
        print(f"  API请求失败: {poi_name}, 错误: {e}")
        return None


def parse_location(location_str: str) -> tuple[float, float] | None:
    """
    Parse Amap location string in "lng,lat" format
    Returns: (lng, lat) or None
    """
    if not location_str:
        return None
    try:
        parts = location_str.split(",")
        lng = float(parts[0])
        lat = float(parts[1])
        return (lng, lat)
    except (ValueError, IndexError):
        return None


def parse_categories(type_str: str) -> list[str]:
    """
    Parse Amap type string, e.g. "科教文化服务;会展中心;会展中心"
    Returns deduplicated category list
    """
    if not type_str:
        return []

    categories = set()
    # type may contain multiple categories, separated by |
    for type_group in type_str.split("|"):
        # Each category group is separated by ;
        parts = type_group.split(";")
        for part in parts:
            part = part.strip()
            if part:
                categories.add(part)

    return list(categories)


def extract_images(photos: list[dict] | None) -> list[str]:
    """Extract image URL list"""
    if not photos:
        return []
    return [p.get("url") for p in photos if p.get("url")]


def generate_id() -> str:
    """Generate unique ID using UUID7"""
    return str(uuid7())


def convert_to_poi_doc(original_poi: dict, amap_poi: dict | None) -> dict:
    """
    Convert original POI and Amap data to PoiDoc format.

    The 'createdAt' and 'updatedAt' fields are set to the current UTC time so
    that the document is consistent with Spring Data's @CreatedDate /
    @LastModifiedDate semantics even when inserted directly via Python.
    Both are stored as ISO-8601 strings; pois.py converts them to BSON Dates
    at import time.
    """
    name = original_poi.get("name", "")
    original_position = original_poi.get("position", [])

    # Default to using original coordinates (position is in [lat, lng] format)
    if len(original_position) >= 2:
        lat, lng = original_position[0], original_position[1]
    else:
        lat, lng = 0, 0

    # Timestamps — use the same instant for both fields on first creation
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # Base structure, generate ID using UUID7.
    # Use '_id' directly as the field name so the document can be inserted
    # into MongoDB without any transformation.
    poi_doc = {
        "_id": generate_id(),
        "name": name,
        "location": {
            "type": "Point",
            "coordinates": [lng, lat],  # GeoJSON format: [lng, lat]
        },
        "address": {"province": "", "city": "", "district": "", "detailed": ""},
        "adcode": "",
        "amapId": "",
        "categories": [],
        "images": [],
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }

    # If Amap data is available, supplement detailed information
    if amap_poi:
        # Use Amap coordinates (more accurate)
        amap_location = parse_location(amap_poi.get("location", ""))
        if amap_location:
            poi_doc["location"]["coordinates"] = list(amap_location)

        # Address information
        poi_doc["address"] = {
            "province": amap_poi.get("pname", ""),
            "city": amap_poi.get("cityname", ""),
            "district": amap_poi.get("adname", ""),
            "detailed": amap_poi.get("address", ""),
        }

        # Other information
        poi_doc["adcode"] = amap_poi.get("adcode", "")
        poi_doc["amapId"] = amap_poi.get("id", "")
        poi_doc["categories"] = parse_categories(amap_poi.get("type", ""))
        poi_doc["images"] = extract_images(amap_poi.get("photos"))

    return poi_doc


def enrich_pois(
    original_pois: list[dict], amap_pois: list[dict], api_key: str | None
) -> tuple[list[dict], list[dict]]:
    """
    Enrich all POI information
    Returns: (enriched_pois, unmatched_pois)
    """
    # Build Amap data index
    print("正在构建Amap数据索引...")
    exact_index, core_index = build_amap_index(amap_pois)
    print(f"精确索引: {len(exact_index)} 个POI, 核心索引: {len(core_index)} 个条目")

    enriched_pois = []
    unmatched_pois = []
    api_results = {}  # Cache API results

    # Try to load previous API result cache
    if API_RESULTS_FILE.exists():
        try:
            api_results = load_json(API_RESULTS_FILE)
            print(f"已加载 {len(api_results)} 条API缓存结果")
        except Exception:
            pass

    total = len(original_pois)
    for i, poi in enumerate(original_pois, 1):
        name = poi.get("name", "")
        print(f"[{i}/{total}] 处理: {name}")

        # 1. First search in pre-scraped data
        amap_poi = find_in_amap_data(name, exact_index, core_index)

        if amap_poi:
            matched_name = amap_poi.get("name", "")
            if matched_name == name:
                print("  ✓ 精确匹配")
            else:
                print(f"  ✓ 匹配到: {matched_name}")
        else:
            # 2. Check API cache
            if name in api_results:
                amap_poi = api_results[name]
                print("  ✓ 使用API缓存结果")
            elif api_key:
                # 3. Call API search (returns first result)
                amap_poi = search_amap_api(name, api_key)
                if amap_poi:
                    api_results[name] = amap_poi
                    # Save intermediate results
                    save_json(api_results, API_RESULTS_FILE)
                # Avoid API requests being too fast
                time.sleep(0.5)

        if not amap_poi:
            print("  ✗ 未找到匹配数据")
            unmatched_pois.append(poi)

        # Convert to PoiDoc format
        poi_doc = convert_to_poi_doc(poi, amap_poi)
        enriched_pois.append(poi_doc)

    return enriched_pois, unmatched_pois


def main():
    print("=" * 60)
    print("POI信息补充脚本")
    print("=" * 60)

    # Load environment variables
    api_key = load_env()
    if api_key:
        print(f"已加载Amap API Key: {api_key[:8]}...")

    # Ensure directories exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load original POI data
    print(f"\n加载原始POI数据: {ORIGINAL_POI_FILE}")
    original_pois = load_json(ORIGINAL_POI_FILE)
    print(f"共 {len(original_pois)} 个POI")

    # Load pre-scraped Amap data
    print(f"\n加载Amap预爬取数据: {AMAP_POIS_FILE}")
    amap_pois = load_json(AMAP_POIS_FILE)
    print(f"共 {len(amap_pois)} 个Amap POI")

    # Enrich POI information
    print("\n开始补充POI信息...")
    print("-" * 40)
    enriched_pois, unmatched_pois = enrich_pois(original_pois, amap_pois, api_key)

    # Save results
    print("\n" + "-" * 40)
    print("保存结果...")
    save_json(enriched_pois, OUTPUT_FILE)

    # Save unmatched POIs (for inspection)
    if unmatched_pois:
        save_json(unmatched_pois, UNMATCHED_FILE)
        print(f"警告: {len(unmatched_pois)} 个POI未找到匹配数据")

    # Statistics
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  总POI数: {len(original_pois)}")
    print(f"  成功补充: {len(original_pois) - len(unmatched_pois)}")
    print(f"  未找到匹配: {len(unmatched_pois)}")
    print(f"  输出文件: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
