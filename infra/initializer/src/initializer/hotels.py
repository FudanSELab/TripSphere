"""
Import / export hotel data for the trip-hotel-service MongoDB collection.

File naming convention
──────────────────────
  raw_hotels.json    Manually collected / scraped hotel data (source)
  hotels.json        Canonical version with stable _id values (source of truth)

Subcommands
───────────

import
    Import hotel documents into MongoDB.  Two input flavours are supported:

    a) Raw hotel JSON (first-time import):
       Documents may have empty ``_id`` fields – MongoDB will generate new
       ObjectIds, and createdAt/updatedAt timestamps are added automatically.
           uv run -m initializer.hotels import data/raw_hotels.json

    b) Canonical hotels.json with ``_id`` (re-import):
       ``_id`` strings are converted back to ObjectId so the exact same IDs
       are restored.  ISO timestamp strings are also restored to datetime.
           uv run -m initializer.hotels import data/hotels.json

export
    Dump hotel_db.hotels to a JSON file with ``_id`` serialised as 24-char
    hex strings.  The output (default: data/hotels.json) becomes the canonical
    source-of-truth for future deployments.

        uv run -m initializer.hotels export
        uv run -m initializer.hotels export --output data/hotels.json

hotels.json field conventions
─────────────────────────────
  _id          : 24-char hex ObjectId string (auto-generated on first import)
  poiId        : 24-char hex string referencing a POI in pois.json
  _poiAmapId   : (fallback) Amap POI ID for runtime resolution
  location     : GeoJSON Point or "longitude,latitude" string
  openingSince : "YYYY"
  estimatedPrice / BreakfastPolicy.price : { "currency": "CNY", "amount": 688 }
  checkInTime / checkOutTime : "HH:MM:SS"
  breakfast    : null → no breakfast offered
  createdAt / updatedAt : ISO-8601 timestamp strings
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

DEFAULT_MONGO_URI = "mongodb://root:fudanse@localhost:27017"
DEFAULT_HOTEL_DB = "hotel_db"
DEFAULT_POI_DB = "poi_db"
DEFAULT_COLLECTION = "hotels"


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string back to a datetime object."""
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


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
    """Look up a POI by its Amap ID."""
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


# ── load / prepare ───────────────────────────────────────────────────────────


def load_hotels(filepath: str) -> list[dict[str, Any]]:
    """
    Load hotel JSON file.

    Handles both raw_hotels.json (empty ``_id``) and canonical hotels.json
    (with ``_id`` and ISO timestamps):
      - Non-empty ``_id`` strings → converted to bson.ObjectId
      - Empty ``_id`` strings → removed (MongoDB will generate)
      - ISO timestamp strings → converted to datetime
    """
    print(f"[INFO] Loading hotel data from {filepath} ...")
    with open(filepath, encoding="utf-8") as f:
        docs: list[dict[str, Any]] = json.load(f)
    print(f"[INFO] Loaded {len(docs)} hotel entries.")

    id_restored = 0
    for doc in docs:
        # _id handling
        raw_id = doc.get("_id")
        if isinstance(raw_id, str) and raw_id:
            doc["_id"] = ObjectId(raw_id)
            id_restored += 1
        elif "_id" in doc:
            # Empty string or None – remove so MongoDB generates a new ObjectId
            del doc["_id"]

        # Timestamps: ISO string → datetime
        for ts_field in ("createdAt", "updatedAt"):
            parsed = _parse_iso_datetime(doc.get(ts_field))
            if parsed:
                doc[ts_field] = parsed

    if id_restored:
        print(f"[INFO] Restored {id_restored} _id values from canonical dump.")

    return docs


def prepare_hotel(
    raw: dict[str, Any],
    poi_collection: Collection | None,
) -> dict[str, Any]:
    """
    Transform a hotel entry into a HotelDoc-compatible document.

    Priority for poiId:
      1. ``poiId`` already present  →  use directly
      2. ``_poiAmapId`` present + poi_collection provided  →  resolve at runtime
      3. Neither present  →  poiId unchanged (may be null)

    Priority for location:
      1. Explicit ``location`` in JSON
      2. Copied from the resolved POI document
      3. null (warning emitted)
    """
    hotel = dict(raw)
    hotel_name: str = hotel.get("name", "?")
    poi_doc: dict[str, Any] | None = None

    # ── poiId: direct or resolved ────────────────────────────────────────────
    poi_amap_id: str | None = hotel.pop("_poiAmapId", None)

    if hotel.get("poiId"):
        # Already set – no lookup needed
        pass
    elif poi_amap_id and poi_collection is not None:
        poi_doc = _resolve_poi(poi_collection, poi_amap_id, hotel_name)
        hotel["poiId"] = str(poi_doc["_id"]) if poi_doc else None

    # ── location ─────────────────────────────────────────────────────────────
    explicit_location = _parse_location(hotel.get("location"))
    if explicit_location:
        hotel["location"] = explicit_location
    elif poi_doc and poi_doc.get("location"):
        hotel["location"] = poi_doc["location"]
    elif hotel.get("location") is None:
        print(
            f"[WARN] No location for hotel={hotel_name!r}; 2dsphere index requires one."
        )

    return hotel


# ── import ───────────────────────────────────────────────────────────────────


def import_hotels(
    filepath: str,
    mongo_uri: str = DEFAULT_MONGO_URI,
    hotel_db_name: str = DEFAULT_HOTEL_DB,
    poi_db_name: str = DEFAULT_POI_DB,
    collection_name: str = DEFAULT_COLLECTION,
    clear: bool = False,
) -> None:
    docs = load_hotels(filepath)
    if not docs:
        print("[WARN] No valid documents to import. Exiting.")
        return

    # ── Connect ──────────────────────────────────────────────────────────────
    print(f"[INFO] Connecting to MongoDB at {mongo_uri} ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")
    print("[INFO] Connected.")

    poi_collection: Collection = client[poi_db_name]["pois"]
    hotel_collection: Collection = client[hotel_db_name][collection_name]

    if clear:
        deleted = hotel_collection.delete_many({}).deleted_count
        print(f"[INFO] Cleared {deleted} existing documents.")

    # ── Prepare ──────────────────────────────────────────────────────────────
    prepared: list[dict[str, Any]] = []
    for doc in docs:
        try:
            prepared.append(prepare_hotel(doc, poi_collection))
        except Exception as exc:
            print(f"[ERROR] Failed to prepare hotel={doc.get('name', '?')!r}: {exc}")

    if not prepared:
        print("[WARN] No valid hotel documents to insert. Exiting.")
        client.close()
        return

    # Add timestamps if missing
    now = datetime.now(timezone.utc)
    ts_added = 0
    for doc in prepared:
        if doc.get("createdAt") is None:
            doc["createdAt"] = now
            ts_added += 1
        if doc.get("updatedAt") is None:
            doc["updatedAt"] = now
    if ts_added:
        print(f"[INFO] Added timestamps to {ts_added} documents.")

    linked = sum(1 for d in prepared if d.get("poiId"))
    print(f"[INFO] Prepared {len(prepared)} docs — {linked} linked to a POI.")

    # ── Insert ───────────────────────────────────────────────────────────────
    try:
        result = hotel_collection.insert_many(prepared, ordered=False)
        inserted = len(result.inserted_ids)
    except BulkWriteError as exc:
        inserted = exc.details.get("nInserted", 0)
        for err in exc.details.get("writeErrors", []):
            print(f"[WARN] Write error: code={err['code']} {err['errmsg'][:120]}")

    print(
        f"\n[DONE] Inserted {inserted}/{len(prepared)} hotels into {hotel_db_name}.{collection_name}."
    )
    client.close()


# ── export ───────────────────────────────────────────────────────────────────


def export_hotels(
    output_path: str,
    mongo_uri: str = DEFAULT_MONGO_URI,
    hotel_db_name: str = DEFAULT_HOTEL_DB,
    collection_name: str = DEFAULT_COLLECTION,
) -> None:
    """
    Dump hotel_db.hotels to a JSON file with _id and timestamps serialised.
    """
    print(f"[INFO] Connecting to MongoDB at {mongo_uri} ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")

    collection = client[hotel_db_name][collection_name]
    total = collection.count_documents({})
    print(
        f"[INFO] Exporting {total} documents from {hotel_db_name}.{collection_name} ..."
    )

    docs = []
    for doc in collection.find({}):
        # ObjectId → 24-char hex string
        doc["_id"] = str(doc["_id"])

        # datetime → ISO-8601 string
        for ts_field in ("createdAt", "updatedAt"):
            ts_val = doc.get(ts_field)
            if isinstance(ts_val, datetime):
                doc[ts_field] = ts_val.isoformat()

        docs.append(doc)

    client.close()

    print(f"[INFO] Writing to {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=4)

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"[DONE] Exported {len(docs)} hotels → {output_path} ({size_kb:.1f} KB)")


# ── CLI ──────────────────────────────────────────────────────────────────────


def _add_common_args(parser: argparse.ArgumentParser) -> None:
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
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Collection name (default: {DEFAULT_COLLECTION})",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import / export hotel data for trip-hotel-service MongoDB."
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── import subcommand ────────────────────────────────────────────────────
    import_parser = subparsers.add_parser(
        "import", help="Import hotel JSON into MongoDB."
    )
    import_parser.add_argument(
        "filepath",
        help="Input file (raw_hotels.json or hotels.json with _id).",
    )
    _add_common_args(import_parser)
    import_parser.add_argument(
        "--poi-db",
        default=DEFAULT_POI_DB,
        help=f"POI database for _poiAmapId resolution (default: {DEFAULT_POI_DB})",
    )
    import_parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing documents before importing.",
    )

    # ── export subcommand ────────────────────────────────────────────────────
    export_parser = subparsers.add_parser(
        "export",
        help="Export hotel_db.hotels to a JSON file with _id preserved.",
    )
    _add_common_args(export_parser)
    export_parser.add_argument(
        "--output",
        default="data/hotels.json",
        help="Output file path (default: data/hotels.json)",
    )

    args = parser.parse_args()

    if args.command == "export":
        export_hotels(
            output_path=args.output,
            mongo_uri=args.uri,
            hotel_db_name=args.hotel_db,
            collection_name=args.collection,
        )
    elif args.command == "import":
        import_hotels(
            filepath=args.filepath,
            mongo_uri=args.uri,
            hotel_db_name=args.hotel_db,
            poi_db_name=args.poi_db,
            collection_name=args.collection,
            clear=args.clear,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
