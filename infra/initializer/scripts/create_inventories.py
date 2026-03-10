#!/usr/bin/env -S uv run --script
"""
Inventory Data Creation Script

Reads seeded SPU/SKU data from spus.json and generates 120 days of daily
inventory records for hotel room SKUs and attraction ticket SKUs.

The generated JSON is intentionally shaped for Spring Data JPA ingestion and
matches the fields of DailyInventoryEntity:
{
    "id": str (UUID7),
    "skuId": str,
    "invDate": "YYYY-MM-DD",
    "totalQty": int,
    "availableQty": int,
    "lockedQty": int,
    "soldQty": int,
    "priceCurrency": "CNY",
    "priceUnits": int,
    "priceNanos": int,
    "updatedAt": str (ISO-8601 UTC)
}
"""

import hashlib
import json
import random
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
SEEDED_DIR = DATA_DIR / "seeded"

INPUT_SPUS_FILE = SEEDED_DIR / "shanghai" / "spus.json"
OUTPUT_FILE = SEEDED_DIR / "shanghai" / "inventories.json"
SUMMARY_FILE = TEMP_DIR / "inventory_summary.json"

# ---------------------------------------------------------------------------
# Shared UUID7 helper
# ---------------------------------------------------------------------------
sys.path.insert(0, str(BASE_DIR / "src"))
from initializer.utils.uuid import uuid7  # noqa: E402


def generate_id() -> str:
    """Generate a UUID7 string."""
    return str(uuid7())


# ---------------------------------------------------------------------------
# Generation constants
# ---------------------------------------------------------------------------
SEED = 20260309
INVENTORY_DAYS = 120
HOTEL_TOTAL_QTY_RANGE = (5, 15)
ATTRACTION_TOTAL_QTY_RANGE = (100, 500)
WEEKEND_DAYS = {4, 5}  # Friday, Saturday
SUNDAY = 6

# Mainland China public holiday windows within the seeded horizon.
HOLIDAY_WINDOWS: dict[str, tuple[date, date]] = {
    "qingming": (date(2026, 4, 4), date(2026, 4, 6)),
    "labor_day": (date(2026, 5, 1), date(2026, 5, 5)),
    "dragon_boat": (date(2026, 6, 19), date(2026, 6, 21)),
}


@dataclass(frozen=True)
class SkuContext:
    """Flattened SPU/SKU context used by the inventory generator."""

    spu_id: str
    spu_name: str
    spu_status: str
    resource_type: str
    resource_id: str
    sku_id: str
    sku_name: str
    sku_status: str
    base_currency: str
    base_amount: Decimal


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
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def decimal_amount(value: Any) -> Decimal:
    """Convert a raw JSON price amount into a 2-decimal Decimal."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def split_money(amount: Decimal) -> tuple[int, int]:
    """
    Split a decimal amount into protobuf/Spring compatible units and nanos.

    Examples:
        939.00 -> (939, 0)
        939.50 -> (939, 500000000)
    """
    normalized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    units = int(normalized)
    nanos = int((normalized - Decimal(units)) * Decimal("1000000000"))
    return units, nanos


def make_rng(*parts: Any) -> random.Random:
    """
    Build a deterministic random generator from the fixed seed and the given key.

    Python's built-in hash is process-randomised, so a SHA-256 based seed keeps
    the output stable across runs and machines.
    """
    key = "|".join(str(part) for part in (SEED, *parts))
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    seed_int = int.from_bytes(digest[:8], "big")
    return random.Random(seed_int)


def holiday_name(day: date) -> str | None:
    """Return the configured holiday window name for the given date, if any."""
    for name, (start, end) in HOLIDAY_WINDOWS.items():
        if start <= day <= end:
            return name
    return None


def is_weekend(day: date) -> bool:
    """Return True if the given date is Friday/Saturday/Sunday."""
    return day.weekday() in WEEKEND_DAYS or day.weekday() == SUNDAY


def extract_sku_contexts(
    spus: list[dict[str, Any]],
) -> tuple[list[SkuContext], dict[str, int]]:
    """Flatten SPU/SKU documents into inventory-generation contexts."""
    contexts: list[SkuContext] = []
    skipped_inactive_spus = 0
    skipped_inactive_skus = 0
    skipped_missing_price = 0

    for spu in spus:
        spu_status = spu.get("status", "")
        if spu_status != "SPU_STATUS_ON_SHELF":
            skipped_inactive_spus += 1
            continue

        for sku in spu.get("skus", []):
            sku_status = sku.get("status", "")
            if sku_status != "SKU_STATUS_ACTIVE":
                skipped_inactive_skus += 1
                continue

            base_price = sku.get("basePrice") or {}
            amount = base_price.get("amount")
            currency = base_price.get("currency") or "CNY"
            if amount is None:
                skipped_missing_price += 1
                continue

            contexts.append(
                SkuContext(
                    spu_id=spu.get("_id", ""),
                    spu_name=spu.get("name", ""),
                    spu_status=spu_status,
                    resource_type=spu.get("resourceType", ""),
                    resource_id=spu.get("resourceId", ""),
                    sku_id=sku.get("id", ""),
                    sku_name=sku.get("name", ""),
                    sku_status=sku_status,
                    base_currency=currency,
                    base_amount=decimal_amount(amount),
                )
            )

    stats = {
        "skippedInactiveSpus": skipped_inactive_spus,
        "skippedInactiveSkus": skipped_inactive_skus,
        "skippedMissingPrice": skipped_missing_price,
    }
    return contexts, stats


def hotel_total_qty(context: SkuContext, day: date) -> int:
    """Generate a deterministic hotel room stock level for the given day."""
    rng = make_rng("hotel_total", context.sku_id, day.isoformat())
    low, high = HOTEL_TOTAL_QTY_RANGE
    total = rng.randint(low, high)

    name = context.spu_name + " " + context.sku_name
    if "家庭房" in name:
        total = max(low, total - rng.randint(1, 3))
    elif "豪华" in name:
        total = max(low, total - rng.randint(0, 2))

    if day.weekday() in WEEKEND_DAYS:
        total = max(low, total - rng.randint(0, 2))
    elif day.weekday() == SUNDAY:
        total = max(low, total - rng.randint(0, 1))

    if holiday_name(day):
        total = max(low, total - rng.randint(1, 3))

    return total


def attraction_total_qty(context: SkuContext, day: date) -> int:
    """Generate a deterministic attraction ticket stock level for the given day."""
    rng = make_rng("attraction_total", context.sku_id, day.isoformat())
    low, high = ATTRACTION_TOTAL_QTY_RANGE
    total = rng.randint(low, high)

    sku_name = context.sku_name
    if "成人" in sku_name:
        total += rng.randint(20, 60)
    elif "儿童" in sku_name:
        total = max(low, total - rng.randint(20, 80))
    elif "学生" in sku_name:
        total = max(low, total - rng.randint(10, 50))
    elif "老人" in sku_name or "老年" in sku_name:
        total = max(low, total - rng.randint(10, 40))

    if holiday_name(day):
        total += rng.randint(30, 120)
    elif is_weekend(day):
        total += rng.randint(10, 50)

    return min(650, total)


def hotel_price(context: SkuContext, day: date) -> Decimal:
    """Generate a hotel price with deterministic daily fluctuation."""
    rng = make_rng("hotel_price", context.sku_id, day.isoformat())
    multiplier = Decimal("1.00")
    weekday = day.weekday()

    if holiday_name(day):
        multiplier *= Decimal(str(rng.uniform(1.18, 1.36)))
    elif weekday in WEEKEND_DAYS:
        multiplier *= Decimal(str(rng.uniform(1.10, 1.24)))
    elif weekday == SUNDAY:
        multiplier *= Decimal(str(rng.uniform(1.05, 1.16)))
    else:
        multiplier *= Decimal(str(rng.uniform(0.94, 1.08)))

    if "豪华" in context.spu_name:
        multiplier *= Decimal(str(rng.uniform(1.01, 1.05)))
    if "家庭房" in context.spu_name:
        multiplier *= Decimal(str(rng.uniform(1.03, 1.08)))

    price = (context.base_amount * multiplier).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return max(price, Decimal("1.00"))


def attraction_price(context: SkuContext, day: date) -> Decimal:
    """Generate an attraction ticket price with deterministic daily fluctuation."""
    rng = make_rng("attraction_price", context.sku_id, day.isoformat())
    multiplier = Decimal("1.00")

    if holiday_name(day):
        multiplier *= Decimal(str(rng.uniform(1.12, 1.30)))
    elif is_weekend(day):
        multiplier *= Decimal(str(rng.uniform(1.05, 1.18)))
    else:
        multiplier *= Decimal(str(rng.uniform(0.95, 1.06)))

    sku_name = context.sku_name
    if "儿童" in sku_name:
        multiplier *= Decimal(str(rng.uniform(0.88, 0.95)))
    elif "学生" in sku_name:
        multiplier *= Decimal(str(rng.uniform(0.84, 0.93)))
    elif "老人" in sku_name or "老年" in sku_name:
        multiplier *= Decimal(str(rng.uniform(0.80, 0.90)))

    price = (context.base_amount * multiplier).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return max(price, Decimal("0.00"))


def build_inventory_doc(
    context: SkuContext,
    day: date,
    updated_at: str,
) -> dict[str, Any]:
    """Build a DailyInventoryEntity-compatible JSON document."""
    if context.resource_type == "RESOURCE_TYPE_HOTEL_ROOM":
        total_qty = hotel_total_qty(context, day)
        price = hotel_price(context, day)
    elif context.resource_type == "RESOURCE_TYPE_ATTRACTION":
        total_qty = attraction_total_qty(context, day)
        price = attraction_price(context, day)
    else:
        raise ValueError(f"Unsupported resource type: {context.resource_type}")

    price_units, price_nanos = split_money(price)

    return {
        "id": generate_id(),
        "skuId": context.sku_id,
        "invDate": day.isoformat(),
        "totalQty": total_qty,
        "availableQty": total_qty,
        "lockedQty": 0,
        "soldQty": 0,
        "priceCurrency": context.base_currency,
        "priceUnits": price_units,
        "priceNanos": price_nanos,
        "updatedAt": updated_at,
    }


def generate_inventory_data(
    contexts: list[SkuContext],
    start_day: date,
    days: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate inventory records and per-SKU summary rows."""
    updated_at = now_iso()
    inventories: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    total = len(contexts)
    for index, context in enumerate(contexts, 1):
        sku_records: list[dict[str, Any]] = []
        price_min: Decimal | None = None
        price_max: Decimal | None = None
        qty_min: int | None = None
        qty_max: int | None = None

        for offset in range(days):
            day = start_day + timedelta(days=offset)
            doc = build_inventory_doc(context, day, updated_at)
            sku_records.append(doc)

            current_price = Decimal(doc["priceUnits"]) + (
                Decimal(doc["priceNanos"]) / Decimal("1000000000")
            )
            current_qty = int(doc["totalQty"])

            price_min = (
                current_price if price_min is None else min(price_min, current_price)
            )
            price_max = (
                current_price if price_max is None else max(price_max, current_price)
            )
            qty_min = current_qty if qty_min is None else min(qty_min, current_qty)
            qty_max = current_qty if qty_max is None else max(qty_max, current_qty)

        inventories.extend(sku_records)
        summary_rows.append(
            {
                "spuId": context.spu_id,
                "spuName": context.spu_name,
                "resourceType": context.resource_type,
                "resourceId": context.resource_id,
                "skuId": context.sku_id,
                "skuName": context.sku_name,
                "basePrice": {
                    "currency": context.base_currency,
                    "amount": float(context.base_amount),
                },
                "dateRange": {
                    "start": start_day.isoformat(),
                    "end": (start_day + timedelta(days=days - 1)).isoformat(),
                },
                "recordCount": len(sku_records),
                "minTotalQty": qty_min,
                "maxTotalQty": qty_max,
                "minPriceAmount": float(price_min or Decimal("0.00")),
                "maxPriceAmount": float(price_max or Decimal("0.00")),
            }
        )

        print(
            f"[{index:>3}/{total}] {context.resource_type} | "
            f"{context.spu_name} / {context.sku_name} -> {len(sku_records)} days"
        )

    return inventories, summary_rows


def build_summary_document(
    contexts: list[SkuContext],
    summary_rows: list[dict[str, Any]],
    extraction_stats: dict[str, int],
    start_day: date,
    days: int,
) -> dict[str, Any]:
    """Build a compact summary document for validation and debugging."""
    hotel_skus = [c for c in contexts if c.resource_type == "RESOURCE_TYPE_HOTEL_ROOM"]
    attraction_skus = [
        c for c in contexts if c.resource_type == "RESOURCE_TYPE_ATTRACTION"
    ]
    return {
        "seed": SEED,
        "inventoryDays": days,
        "dateRange": {
            "start": start_day.isoformat(),
            "end": (start_day + timedelta(days=days - 1)).isoformat(),
        },
        "totalSkus": len(contexts),
        "hotelRoomSkus": len(hotel_skus),
        "attractionSkus": len(attraction_skus),
        "totalInventoryRecords": len(contexts) * days,
        **extraction_stats,
        "skuDetails": summary_rows,
    }


def main() -> None:
    print("=" * 60)
    print("库存数据生成脚本")
    print("=" * 60)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n加载SPU数据: {INPUT_SPUS_FILE}")
    spus: list[dict[str, Any]] = load_json(INPUT_SPUS_FILE)  # type: ignore[assignment]
    print(f"共 {len(spus)} 个SPU")

    contexts, extraction_stats = extract_sku_contexts(spus)
    print("\n提取可生成库存的SKU...")
    print(f"  酒店/景点可用SKU数: {len(contexts)}")
    print(f"  跳过未上架SPU数   : {extraction_stats['skippedInactiveSpus']}")
    print(f"  跳过非激活SKU数   : {extraction_stats['skippedInactiveSkus']}")
    print(f"  跳过缺少价格SKU数 : {extraction_stats['skippedMissingPrice']}")

    start_day = datetime.now(UTC).date()

    print("\n开始生成每日库存...")
    print(f"  固定随机种子: {SEED}")
    print(f"  生成天数    : {INVENTORY_DAYS}")
    end_day = start_day + timedelta(days=INVENTORY_DAYS - 1)
    print(f"  日期范围    : {start_day} ~ {end_day}")
    print("-" * 40)

    inventories, summary_rows = generate_inventory_data(
        contexts=contexts,
        start_day=start_day,
        days=INVENTORY_DAYS,
    )
    summary = build_summary_document(
        contexts=contexts,
        summary_rows=summary_rows,
        extraction_stats=extraction_stats,
        start_day=start_day,
        days=INVENTORY_DAYS,
    )

    print("\n" + "-" * 40)
    print("保存结果...")
    save_json(inventories, OUTPUT_FILE)
    save_json(summary, SUMMARY_FILE)

    hotel_count = summary["hotelRoomSkus"]
    attraction_count = summary["attractionSkus"]

    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  总SKU数         : {summary['totalSkus']}")
    print(f"  酒店SKU数       : {hotel_count}")
    print(f"  景点SKU数       : {attraction_count}")
    print(f"  库存记录总数    : {summary['totalInventoryRecords']}")
    print(f"  输出文件        : {OUTPUT_FILE}")
    print(f"  摘要文件        : {SUMMARY_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
