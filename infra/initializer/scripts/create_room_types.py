#!/usr/bin/env -S uv run --script
"""
Room Type Data Creation Script

Reads seeded hotel data from hotels.json and generates 2–3 room types per hotel
conforming to the RoomTypeDoc structure expected by trip-hotel-service.

Rules:
  - Every hotel receives a "豪华大床房" (King) and a "标准双床房" (Twin).
  - Hotels whose tags include any family-related keyword (家庭房 / 亲子主题房 /
    亲子 / 儿童乐园) additionally receive a "家庭房" (Family Room).

Output structure (per document):
{
    "_id":             str  (UUID7),
    "hotelId":         str  (references hotels._id),
    "name":            str,
    "areaDescription": str,   e.g. "20-30平方米"
    "bedDescription":  str,   e.g. "1张1.8米大床"
    "maxOccupancy":    int,
    "hasWindow":       bool,
    "images":          [],
    "description":     str,
    "amenities":       [],
    "createdAt":       str (ISO-8601 UTC),
    "updatedAt":       str (ISO-8601 UTC),
}
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
SEEDED_DIR = DATA_DIR / "seeded"

INPUT_HOTELS_FILE = SEEDED_DIR / "shanghai" / "hotels.json"
OUTPUT_FILE = SEEDED_DIR / "shanghai" / "room_types.json"
SUMMARY_FILE = TEMP_DIR / "room_type_summary.json"

# ---------------------------------------------------------------------------
# UUID7 (no fallback — uuid7 is always available in this project)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(BASE_DIR / "src"))
from initializer.utils.uuid import uuid7  # noqa: E402


def generate_id() -> str:
    return str(uuid7())


# ---------------------------------------------------------------------------
# Tag keywords that trigger the addition of a Family Room
# ---------------------------------------------------------------------------
FAMILY_TAG_KEYWORDS = {"家庭房", "亲子主题房", "亲子", "儿童乐园"}


# ---------------------------------------------------------------------------
# Room type templates
# ---------------------------------------------------------------------------
# Each template is a dict of the fields that differ per room type.
# hotelId, _id, createdAt, and updatedAt are injected at generation time.

ROOM_TYPE_KING: dict[str, Any] = {
    "name": "豪华大床房",
    "areaDescription": "20-30平方米",
    "bedDescription": "1张1.8米大床",
    "maxOccupancy": 2,
    "hasWindow": True,
    "description": "宽敞舒适的大床房，配备豪华床品，适合商务出行或情侣入住。",
}

ROOM_TYPE_TWIN: dict[str, Any] = {
    "name": "标准双床房",
    "areaDescription": "20-30平方米",
    "bedDescription": "2张1.2米单人床",
    "maxOccupancy": 2,
    "hasWindow": True,
    "description": "配备两张单人床，空间宽敞，适合朋友或同事出行入住。",
}

ROOM_TYPE_FAMILY: dict[str, Any] = {
    "name": "家庭房",
    "areaDescription": "35-50平方米",
    "bedDescription": "1张1.8米大床+1张1.2米单人床",
    "maxOccupancy": 4,
    "hasWindow": True,
    "description": "宽敞的家庭房型，配备大床及单人床，满足亲子出行需求。",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_json(file_path: Path) -> list | dict:
    """Load a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Path) -> None:
    """Save data as a pretty-printed JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"已保存: {file_path}")


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (millisecond precision)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_family_hotel(hotel: dict) -> bool:
    """Return True if the hotel has any family-related tag."""
    tags: list[str] = hotel.get("tags", [])
    return any(tag in FAMILY_TAG_KEYWORDS for tag in tags)


def build_room_type_doc(template: dict[str, Any], hotel_id: str, ts: str) -> dict:
    """
    Construct a single RoomTypeDoc dict from *template* and the given hotel ID.

    The 'createdAt' and 'updatedAt' fields mirror Spring Data's @CreatedDate /
    @LastModifiedDate semantics; both are set to *ts* on initial creation.
    """
    return {
        "_id": generate_id(),
        "hotelId": hotel_id,
        "name": template["name"],
        "areaDescription": template["areaDescription"],
        "bedDescription": template["bedDescription"],
        "maxOccupancy": template["maxOccupancy"],
        "hasWindow": template["hasWindow"],
        "images": [],
        "description": template["description"],
        "amenities": [],
        "createdAt": ts,
        "updatedAt": ts,
    }


def generate_room_types(
    hotels: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Generate room type documents for every hotel.

    Returns:
        room_types  – flat list of all RoomTypeDoc dicts
        summary     – list of per-hotel summaries (for SUMMARY_FILE)
    """
    room_types: list[dict] = []
    summary: list[dict] = []

    total = len(hotels)
    family_count = 0

    for i, hotel in enumerate(hotels, 1):
        hotel_id: str = hotel["_id"]
        hotel_name: str = hotel.get("name", "")
        ts = now_iso()

        templates = [ROOM_TYPE_KING, ROOM_TYPE_TWIN]

        add_family = is_family_hotel(hotel)
        if add_family:
            templates.append(ROOM_TYPE_FAMILY)
            family_count += 1

        docs = [build_room_type_doc(t, hotel_id, ts) for t in templates]
        room_types.extend(docs)

        print(f"[{i:>3}/{total}] {hotel_name} → {', '.join(d['name'] for d in docs)}")

        summary.append(
            {
                "hotelId": hotel_id,
                "hotelName": hotel_name,
                "roomTypes": [d["name"] for d in docs],
            }
        )

    return room_types, summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("房型数据生成脚本")
    print("=" * 60)

    # Ensure output directories exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load hotels
    print(f"\n加载酒店数据: {INPUT_HOTELS_FILE}")
    hotels: list[dict] = load_json(INPUT_HOTELS_FILE)
    print(f"共 {len(hotels)} 家酒店\n")

    # Generate room types
    print("开始生成房型数据...")
    print("-" * 40)
    room_types, summary = generate_room_types(hotels)

    # Counters
    family_hotel_count = sum(1 for s in summary if "家庭房" in s["roomTypes"])
    standard_count = len(hotels) - family_hotel_count

    # Save results
    print("\n" + "-" * 40)
    print("保存结果...")
    save_json(room_types, OUTPUT_FILE)
    save_json(summary, SUMMARY_FILE)

    # Statistics
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  总酒店数:            {len(hotels)}")
    print(f"  仅生成2种房型的酒店: {standard_count}")
    print(f"  额外生成家庭房的酒店: {family_hotel_count}")
    print(f"  生成房型文档总数:    {len(room_types)}")
    print(f"  输出文件: {OUTPUT_FILE}")
    print(f"  摘要文件: {SUMMARY_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
