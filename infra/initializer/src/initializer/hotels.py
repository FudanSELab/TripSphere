"""
Seed hotel data into trip-hotel-service MongoDB (hotel_db.hotels).

hotels.json supports two ways to specify the linked POI:

  1. poiId (preferred after running `pois export`)
     ─────────────────────────────────────────────
     Directly set the 24-char hex ObjectId string that was written into
     pois_seeded.json.  No DB lookup needed at seed time.

         { "poiId": "67c1a3fabcdef1234567890a", ... }

  2. _poiAmapId (fallback / convenience during development)
     ────────────────────────────────────────────────────────
     If ``poiId`` is absent the script resolves ``_poiAmapId`` (the Amap
     POI ID) against poi_db.pois at runtime.  Useful before pois_seeded.json
     has been generated, or to fill in hotels quickly by Amap keyword search.

         { "_poiAmapId": "B0FFFDXOI4", ... }

     To find the right amapId, run in mongosh:
         db.pois.find(
           { name: { $regex: "希尔顿", $options: "i" } },
           { _id: 0, amapId: 1, name: 1 }
         ).limit(5)

hotels.json field conventions
──────────────────────────────
  poiId        : 24-char hex string from pois_seeded.json  (preferred)
  _poiAmapId   : Amap POI ID for runtime resolution        (fallback)
  location     : optional "longitude,latitude"; copied from POI if absent
  openingDate  : "YYYY-MM-DD"
  estimatedPrice / BreakfastPolicy.price : { "currency": "CNY", "amount": 688 }
  checkInTime / checkOutTime : "HH:MM:SS"
  breakfast    : null → no breakfast offered

Usage
─────
    uv run -m initializer.hotels data/hotels.json
    uv run -m initializer.hotels data/hotels.json --clear
"""

import argparse
import json
import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

DEFAULT_MONGO_URI = "mongodb://root:fudanse@localhost:27017"
DEFAULT_HOTEL_DB = "hotel_db"
DEFAULT_POI_DB = "poi_db"
DEFAULT_COLLECTION = "hotels"


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_location(raw_location: Any) -> dict[str, Any] | None:
    """
    Accept a "longitude,latitude" string and return a GeoJSON Point dict.
    Returns None (silently) if the value is absent or unparseable.
    """
    if not raw_location:
        return None
    if isinstance(raw_location, dict):
        # Already GeoJSON (e.g. copied from POI document)
        return raw_location if raw_location.get("type") == "Point" else None
    try:
        lon_str, lat_str = str(raw_location).split(",")
        return {
            "type": "Point",
            "coordinates": [float(lon_str.strip()), float(lat_str.strip())],
        }
    except (ValueError, AttributeError):
        return None


def _resolve_poi(
    poi_collection: Collection,
    amap_id: str,
    hotel_name: str,
) -> dict[str, Any] | None:
    """
    Look up a POI by its Amap ID.  Returns the raw MongoDB document on
    success, or None with a helpful warning (including a mongosh query
    the developer can run to find the correct amapId).
    """
    doc = poi_collection.find_one({"amapId": amap_id})
    if doc:
        return doc

    print(
        f"[WARN] POI not found for _poiAmapId={amap_id!r}  (hotel: {hotel_name!r})\n"
        f"       → poiId will be null.  To find the correct amapId, run in mongosh:\n"
        f'           db.pois.find({{name:{{$regex:"{hotel_name[:6]}"}}}}, '
        f"{{_id:0,amapId:1,name:1}}).limit(5)"
    )
    return None


def prepare_hotel(
    raw: dict[str, Any],
    poi_collection: Collection,
) -> dict[str, Any]:
    """
    Transform a raw hotels.json entry into a HotelDoc-compatible document.

    Priority for poiId:
      1. ``poiId`` already present in the JSON  →  use directly (fast path,
         no DB lookup; requires pois_seeded.json to have been generated first).
      2. ``_poiAmapId`` present  →  resolve against poi_db at runtime (fallback).
      3. Neither present  →  poiId = null, warning emitted.

    Priority for location:
      1. Explicit ``location`` string in JSON
      2. Copied from the resolved POI document
      3. null  (warning emitted)
    """
    hotel = dict(raw)
    hotel_name: str = hotel.get("name", "?")
    poi_doc: dict[str, Any] | None = None

    # ── 1. poiId: direct or resolved ────────────────────────────────────────
    poi_amap_id: str | None = hotel.pop("_poiAmapId", None)

    if hotel.get("poiId"):
        # Already set in hotels.json — no DB lookup needed.
        pass
    elif poi_amap_id:
        # Fallback: resolve Amap ID → MongoDB _id
        poi_doc = _resolve_poi(poi_collection, poi_amap_id, hotel_name)
        hotel["poiId"] = str(poi_doc["_id"]) if poi_doc else None
    else:
        hotel["poiId"] = None

    # ── 2. location ──────────────────────────────────────────────────────────
    explicit_location = _parse_location(hotel.get("location"))
    if explicit_location:
        hotel["location"] = explicit_location
    elif poi_doc and poi_doc.get("location"):
        hotel["location"] = poi_doc["location"]
    else:
        hotel["location"] = None
        print(
            f"[WARN] No location resolved for hotel={hotel_name!r}; 2dsphere index requires one."
        )

    return hotel


# ── main logic ────────────────────────────────────────────────────────────────


def seed_hotels(
    filepath: str,
    mongo_uri: str = DEFAULT_MONGO_URI,
    hotel_db_name: str = DEFAULT_HOTEL_DB,
    poi_db_name: str = DEFAULT_POI_DB,
    collection_name: str = DEFAULT_COLLECTION,
    clear: bool = False,
) -> None:
    # ── Load seed file ───────────────────────────────────────────────────────
    print(f"[INFO] Reading seed file: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        raw_hotels: list[dict[str, Any]] = json.load(f)
    print(f"[INFO] Loaded {len(raw_hotels)} hotel entries.")

    # ── Connect ──────────────────────────────────────────────────────────────
    print(f"[INFO] Connecting to MongoDB at {mongo_uri} ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")
    print("[INFO] Connected.")

    poi_collection: Collection = client[poi_db_name]["pois"]
    hotel_collection: Collection = client[hotel_db_name][collection_name]

    if clear:
        deleted = hotel_collection.delete_many({}).deleted_count
        print(
            f"[INFO] Cleared {deleted} existing documents from {hotel_db_name}.{collection_name}."
        )

    # ── Prepare & insert ─────────────────────────────────────────────────────
    docs: list[dict[str, Any]] = []
    for raw in raw_hotels:
        try:
            docs.append(prepare_hotel(raw, poi_collection))
        except Exception as exc:
            print(f"[ERROR] Failed to prepare hotel={raw.get('name', '?')!r}: {exc}")

    if not docs:
        print("[WARN] No valid hotel documents to insert. Exiting.")
        client.close()
        return

    linked = sum(1 for d in docs if d.get("poiId"))
    unlinked = len(docs) - linked
    print(
        f"[INFO] Prepared {len(docs)} documents — "
        f"{linked} linked to a POI, {unlinked} without poiId."
    )

    try:
        result = hotel_collection.insert_many(docs, ordered=False)
        inserted = len(result.inserted_ids)
    except BulkWriteError as exc:
        inserted = exc.details.get("nInserted", 0)
        for err in exc.details.get("writeErrors", []):
            print(f"[WARN] Write error: code={err['code']} {err['errmsg'][:120]}")

    print(
        f"\n[DONE] Inserted {inserted}/{len(docs)} hotels "
        f"into {hotel_db_name}.{collection_name}."
    )
    client.close()


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed hotel data into trip-hotel-service MongoDB, resolving poiId from poi_db."
    )
    parser.add_argument("filepath", help="Path to hotels.json seed file")
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGO_URI", DEFAULT_MONGO_URI),
        help=f"MongoDB URI (env: MONGO_URI, default: {DEFAULT_MONGO_URI})",
    )
    parser.add_argument(
        "--hotel-db",
        default=DEFAULT_HOTEL_DB,
        help=f"Hotel database name (default: {DEFAULT_HOTEL_DB})",
    )
    parser.add_argument(
        "--poi-db",
        default=DEFAULT_POI_DB,
        help=f"POI database name to resolve _poiAmapId (default: {DEFAULT_POI_DB})",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Hotel collection name (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing documents in the collection before seeding",
    )
    args = parser.parse_args()

    seed_hotels(
        filepath=args.filepath,
        mongo_uri=args.uri,
        hotel_db_name=args.hotel_db,
        poi_db_name=args.poi_db,
        collection_name=args.collection,
        clear=args.clear,
    )


if __name__ == "__main__":
    main()
