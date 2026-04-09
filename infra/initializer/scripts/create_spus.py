#!/usr/bin/env -S uv run --script
"""
SPU/SKU Data Creation Script

Reads seeded hotel, room-type, and attraction data and produces SPU
(Standard Product Unit) documents with embedded SKU (Stock Keeping Unit)
sub-documents, conforming to the SpuDoc / SkuDoc structure expected by
trip-product-service (Spring Data MongoDB).

Generation rules
────────────────
Hotel room types  (resourceType = RESOURCE_TYPE_HOTEL_ROOM):
  • One SPU per room type, one embedded SKU ("标准入住").
  • Base price is derived from the hotel's estimatedPrice, which originates
    from the accommodation CSV and represents the cheapest nightly rate at
    that property.  Price multipliers per room type:
      豪华大床房  → 1.0 × estimatedPrice
      标准双床房  → 1.0 × estimatedPrice
      家庭房      → 1.5 × estimatedPrice  (rounded to nearest integer)

Attractions  (resourceType = RESOURCE_TYPE_ATTRACTION):
  • Only paid attractions (ticketInfo.estimatedPrice.amount > 0) get a SPU.
  • Free attractions are skipped (no ticket needed).
  • One SPU per attraction, named "<景点名> 一日票", with two embedded SKUs:
      成人票  → ticketInfo.estimatedPrice.amount
      儿童票  → max(round(adult_price × 0.5), 1)

Output document structure (SpuDocument)
───────────────────────────────────────
{
    "_id":          str   UUID7
    "name":         str
    "description":  str
    "resourceType": "HOTEL_ROOM" | "ATTRACTION"
    "resourceId":   str   (room-type _id  OR  attraction _id)
    "images":       []
    "status":       "ON_SHELF"
    "attributes":   null
    "skus": [
        {
            "id":          str   UUID7
            "name":        str
            "spuId":       str   (back-reference to parent SPU _id)
            "description": str
            "status":      "ACTIVE"
            "attributes":  null
            "basePrice":   {"currency": "CNY", "amount": float}
        }
    ]
}

Notes on Spring Data MongoDB compatibility
───────────────────────────────────────────
• resourceType and status are plain String fields in SpuDocument / SkuDocument.
  Values are the domain enum names (e.g. "HOTEL_ROOM", "ON_SHELF", "ACTIVE"),
  NOT the proto enum names with prefixes.
• basePrice.amount is stored here as a plain Python float.  The downstream
  importer should convert it to BSON Decimal128 so that Spring Data maps it
  correctly to java.math.BigDecimal.
"""

import json
import sys
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
INPUT_ROOM_TYPES_FILE = SEEDED_DIR / "shanghai" / "room_types.json"
INPUT_ATTRACTIONS_FILE = SEEDED_DIR / "shanghai" / "attractions.json"
OUTPUT_FILE = SEEDED_DIR / "shanghai" / "spus.json"
SUMMARY_FILE = TEMP_DIR / "spus_summary.json"

# ---------------------------------------------------------------------------
# UUID7 (imported from shared utils — always available in this project)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(BASE_DIR / "src"))
from initializer.utils.uuid import uuid7  # noqa: E402


def generate_id() -> str:
    return str(uuid7())


# ---------------------------------------------------------------------------
# Domain enum names — stored as strings by SpuDocumentMapper (MapStruct)
# ---------------------------------------------------------------------------
RESOURCE_TYPE_HOTEL_ROOM = "HOTEL_ROOM"
RESOURCE_TYPE_ATTRACTION = "ATTRACTION"
SPU_STATUS_ON_SHELF = "ON_SHELF"
SKU_STATUS_ACTIVE = "ACTIVE"

# ---------------------------------------------------------------------------
# Price multiplier per room-type name
# ---------------------------------------------------------------------------
ROOM_PRICE_MULTIPLIER: dict[str, float] = {
    "豪华大床房": 1.0,
    "标准双床房": 1.0,
    "家庭房": 1.5,
}
DEFAULT_ROOM_MULTIPLIER: float = 1.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_json(file_path: Path) -> list | dict:
    """Load a JSON file and return the parsed object."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Path) -> None:
    """Persist *data* as a pretty-printed UTF-8 JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"已保存: {file_path}")


def build_money(amount: float) -> dict[str, Any]:
    """
    Build a Money sub-document compatible with the Java Money record.

    Spring Data serialises java.util.Currency as its ISO-4217 code string
    and java.math.BigDecimal as BSON Decimal128.  The downstream importer
    is responsible for the Decimal128 conversion; here we store a plain float.
    """
    return {"currency": "CNY", "amount": round(amount, 2)}


def build_sku_doc(
    name: str, description: str, amount: float, spu_id: str
) -> dict[str, Any]:
    """Construct a single SkuDoc sub-document."""
    return {
        "id": generate_id(),
        "name": name,
        "spuId": spu_id,
        "description": description,
        "status": SKU_STATUS_ACTIVE,
        "attributes": None,
        "basePrice": build_money(amount),
    }


def build_spu_doc(
    spu_id: str,
    name: str,
    description: str,
    resource_type: str,
    resource_id: str,
    skus: list[dict[str, Any]],
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct a single SpuDocument document."""
    return {
        "_id": spu_id,
        "name": name,
        "description": description,
        "resourceType": resource_type,
        "resourceId": resource_id,
        "images": [],
        "status": SPU_STATUS_ON_SHELF,
        "attributes": attributes,
        "skus": skus,
    }


# ---------------------------------------------------------------------------
# Hotel-room SPU generation
# ---------------------------------------------------------------------------


def build_hotel_price_index(hotels: list[dict]) -> dict[str, float]:
    """
    Build a hotel_id → base_price mapping.

    The base price is the hotel's estimatedPrice.amount, which matches the
    'price' column from accommodations.csv and represents the cheapest nightly
    rate available at that property.
    """
    index: dict[str, float] = {}
    for hotel in hotels:
        hotel_id: str | None = hotel.get("_id")
        price_doc: dict = hotel.get("estimatedPrice") or {}
        amount = price_doc.get("amount")
        if hotel_id and amount is not None:
            try:
                index[hotel_id] = float(amount)
            except (TypeError, ValueError):
                pass
    return index


def generate_hotel_spus(
    room_types: list[dict],
    hotel_price_index: dict[str, float],
) -> tuple[list[dict], list[dict]]:
    """
    Generate one SpuDoc (with one embedded SkuDoc) per room type.

    The SKU price is computed as:
        sku_price = round(hotel_base_price × ROOM_PRICE_MULTIPLIER[room_name])

    Returns:
        spus     – flat list of SpuDoc dicts
        summary  – per-entry summary rows for SUMMARY_FILE
    """
    spus: list[dict] = []
    summary: list[dict] = []
    skipped = 0
    total = len(room_types)

    for i, rt in enumerate(room_types, 1):
        room_type_id: str = rt["_id"]
        hotel_id: str = rt.get("hotelId", "")
        room_name: str = rt.get("name", "")
        room_desc: str = rt.get("description", "")

        base_price = hotel_price_index.get(hotel_id)
        if base_price is None:
            print(
                f"[{i:>4}/{total}] ⚠  跳过房型 '{room_name}' "
                f"(hotelId={hotel_id} 无价格数据)"
            )
            skipped += 1
            continue

        multiplier = ROOM_PRICE_MULTIPLIER.get(room_name, DEFAULT_ROOM_MULTIPLIER)
        sku_price = float(round(base_price * multiplier))

        spu_id = generate_id()
        sku = build_sku_doc(
            name="标准入住",
            description="按入住日期计算，价格为单晚费用。",
            amount=sku_price,
            spu_id=spu_id,
        )
        spu = build_spu_doc(
            spu_id=spu_id,
            name=room_name,
            description=room_desc,
            resource_type=RESOURCE_TYPE_HOTEL_ROOM,
            resource_id=room_type_id,
            skus=[sku],
            attributes={"hotel_id": hotel_id},
        )
        spus.append(spu)
        summary.append(
            {
                "spuId": spu["_id"],
                "skuId": sku["id"],
                "resourceType": RESOURCE_TYPE_HOTEL_ROOM,
                "name": room_name,
                "hotelId": hotel_id,
                "roomTypeId": room_type_id,
                "baseHotelPrice": base_price,
                "multiplier": multiplier,
                "skuPrice": sku_price,
            }
        )

        print(
            f"[{i:>4}/{total}] 酒店房型  {room_name:<10}  "
            f"¥{base_price:.0f} × {multiplier:.1f} = ¥{sku_price:.0f}"
        )

    if skipped:
        print(f"\n⚠  跳过 {skipped} 条房型记录（缺少酒店价格数据）")
    return spus, summary


# ---------------------------------------------------------------------------
# Attraction SPU generation
# ---------------------------------------------------------------------------


def generate_attraction_spus(
    attractions: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Generate one SpuDoc (with two embedded SkuDocs) per paid attraction.

    Free attractions (estimatedPrice.amount == 0 or absent) are skipped.

    Returns:
        spus     – flat list of SpuDoc dicts
        summary  – per-entry summary rows for SUMMARY_FILE
    """
    spus: list[dict] = []
    summary: list[dict] = []
    skipped_free = 0
    total = len(attractions)

    for i, attr in enumerate(attractions, 1):
        attr_id: str = attr["_id"]
        attr_name: str = attr.get("name", "")

        ticket_info: dict = attr.get("ticketInfo") or {}
        price_doc: dict = ticket_info.get("estimatedPrice") or {}
        adult_price_raw = price_doc.get("amount", 0)

        try:
            adult_price = float(adult_price_raw)
        except (TypeError, ValueError):
            adult_price = 0.0

        if adult_price <= 0:
            print(f"[{i:>3}/{total}] ○ 免票景点，跳过  {attr_name}")
            skipped_free += 1
            continue

        child_price = float(max(round(adult_price * 0.5), 1))

        spu_id = generate_id()
        skus = [
            build_sku_doc(
                name="成人票",
                description="适用于18岁及以上成人，含景区一日入场资格。",
                amount=adult_price,
                spu_id=spu_id,
            ),
            build_sku_doc(
                name="儿童票",
                description="适用于18岁以下儿童，含景区一日入场资格。",
                amount=child_price,
                spu_id=spu_id,
            ),
        ]
        spu = build_spu_doc(
            spu_id=spu_id,
            name=f"{attr_name} 一日票",
            description=f"{attr_name}一日游门票，含景区基本入场权益。",
            resource_type=RESOURCE_TYPE_ATTRACTION,
            resource_id=attr_id,
            skus=skus,
        )
        spus.append(spu)
        summary.append(
            {
                "spuId": spu["_id"],
                "adultSkuId": skus[0]["id"],
                "childSkuId": skus[1]["id"],
                "resourceType": RESOURCE_TYPE_ATTRACTION,
                "name": spu["name"],
                "attractionId": attr_id,
                "adultPrice": adult_price,
                "childPrice": child_price,
            }
        )

        print(
            f"[{i:>3}/{total}] 景点门票  {attr_name:<24}  "
            f"成人 ¥{adult_price:.0f}  儿童 ¥{child_price:.0f}"
        )

    return spus, summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("SPU / SKU 数据生成脚本")
    print("=" * 60)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ── Load inputs ───────────────────────────────────────────────────────────
    print(f"\n加载酒店数据:   {INPUT_HOTELS_FILE}")
    hotels: list[dict] = load_json(INPUT_HOTELS_FILE)  # type: ignore[assignment]
    print(f"  共 {len(hotels)} 家酒店")

    print(f"\n加载房型数据:   {INPUT_ROOM_TYPES_FILE}")
    room_types: list[dict] = load_json(INPUT_ROOM_TYPES_FILE)  # type: ignore[assignment]
    print(f"  共 {len(room_types)} 种房型")

    print(f"\n加载景点数据:   {INPUT_ATTRACTIONS_FILE}")
    attractions: list[dict] = load_json(INPUT_ATTRACTIONS_FILE)  # type: ignore[assignment]
    print(f"  共 {len(attractions)} 个景点")

    # ── Build hotel price index ───────────────────────────────────────────────
    print("\n构建酒店价格索引...")
    hotel_price_index = build_hotel_price_index(hotels)
    print(f"  已索引 {len(hotel_price_index)} 家酒店价格")

    # ── Generate hotel-room SPUs ──────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("生成酒店房型 SPU / SKU...")
    print("─" * 60)
    hotel_spus, hotel_summary = generate_hotel_spus(room_types, hotel_price_index)

    # ── Generate attraction SPUs ──────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("生成景点门票 SPU / SKU...")
    print("─" * 60)
    attraction_spus, attraction_summary = generate_attraction_spus(attractions)

    # ── Merge and save ────────────────────────────────────────────────────────
    all_spus = hotel_spus + attraction_spus
    full_summary = {
        "hotel_spus": hotel_summary,
        "attraction_spus": attraction_summary,
    }

    print("\n" + "─" * 60)
    print("保存结果...")
    save_json(all_spus, OUTPUT_FILE)
    save_json(full_summary, SUMMARY_FILE)

    # ── Statistics ────────────────────────────────────────────────────────────
    hotel_sku_count = sum(len(s["skus"]) for s in hotel_spus)
    attraction_sku_count = sum(len(s["skus"]) for s in attraction_spus)
    free_count = len(attractions) - len(attraction_spus)

    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  酒店房型 SPU 数:      {len(hotel_spus)}")
    print(f"  酒店房型 SKU 数:      {hotel_sku_count}")
    print(f"  景点门票 SPU 数:      {len(attraction_spus)}")
    print(f"  景点门票 SKU 数:      {attraction_sku_count}  (成人票 + 儿童票各一)")
    print(f"  免票景点（已跳过）:    {free_count}")
    print(f"  SPU 总数:             {len(all_spus)}")
    print(f"  SKU 总数:             {hotel_sku_count + attraction_sku_count}")
    print(f"  输出文件:             {OUTPUT_FILE}")
    print(f"  摘要文件:             {SUMMARY_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
