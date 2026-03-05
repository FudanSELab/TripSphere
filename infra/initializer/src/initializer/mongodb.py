"""
Import POI data into the trip-poi-service MongoDB collection.

Two workflows are supported:

1. Raw Amap data  (default)
   The input file is a raw pois.json scraped from Amap.
   Conversion runs automatically before importing.

       uv run python -m initializer.mongodb data/pois.json

2. Pre-converted data  (--no-convert)
   The input file was already produced by `initializer.convert`, so the
   conversion step is skipped.  This is the fast path for repeated imports.

       # Step 1 - convert once and save
       uv run python -m initializer.convert data/pois.json
       # → writes data/pois_converted.json

       # Step 2 - import any number of times without re-converting
       uv run python -m initializer.mongodb data/pois_converted.json --no-convert

Options:
    --uri         MongoDB connection URI  (default: mongodb://root:fudanse@localhost:27017)
    --db          Database name          (default: poi_db)
    --collection  Collection name        (default: pois)
    --batch-size  Documents per batch    (default: 1000)
    --no-convert  Skip conversion; input file is already in PoiDoc format
    --clear       Delete existing docs before importing (use with caution!)
"""

import argparse
import json
import os
import time

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from initializer.convert import load_and_convert

# ── Defaults (match trip-poi-service application.yaml) ─────────────────────
DEFAULT_MONGO_URI = "mongodb://root:fudanse@localhost:27017"
DEFAULT_DB = "poi_db"
DEFAULT_COLLECTION = "pois"
DEFAULT_BATCH_SIZE = 1000


def load_converted(filepath: str) -> list[dict]:
    """Load a pre-converted PoiDoc JSON file (produced by initializer.convert)."""
    print(f"[INFO] Loading pre-converted data from {filepath} ...")
    with open(filepath, encoding="utf-8") as f:
        docs: list[dict] = json.load(f)
    print(f"[INFO] Loaded {len(docs)} pre-converted records.")
    return docs


def import_pois(
    filepath: str,
    mongo_uri: str = DEFAULT_MONGO_URI,
    db_name: str = DEFAULT_DB,
    collection_name: str = DEFAULT_COLLECTION,
    batch_size: int = DEFAULT_BATCH_SIZE,
    clear: bool = False,
    no_convert: bool = False,
) -> None:
    # ── Load (and optionally convert) ────────────────────────────────────────
    docs = load_converted(filepath) if no_convert else load_and_convert(filepath)
    if not docs:
        print("[WARN] No valid documents to import. Exiting.")
        return

    # ── Connect ──────────────────────────────────────────────────────────────
    print(f"[INFO] Connecting to MongoDB at {mongo_uri} ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    # Trigger a round-trip to catch connection errors early
    client.admin.command("ping")
    print("[INFO] Connected.")

    collection = client[db_name][collection_name]

    if clear:
        deleted = collection.delete_many({}).deleted_count
        print(
            f"[INFO] Cleared {deleted} existing documents from {db_name}.{collection_name}."
        )

    # ── Batch insert ─────────────────────────────────────────────────────────
    total_inserted = 0
    total_errors = 0
    start = time.perf_counter()

    for batch_idx, offset in enumerate(range(0, len(docs), batch_size), start=1):
        batch = docs[offset : offset + batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            total_inserted += len(result.inserted_ids)
        except BulkWriteError as exc:
            inserted_in_batch = exc.details.get("nInserted", 0)
            total_inserted += inserted_in_batch
            total_errors += len(exc.details.get("writeErrors", []))
            # Log only the first error per batch to avoid log flooding
            first_err = exc.details["writeErrors"][0]
            print(
                f"[WARN] Batch {batch_idx}: inserted {inserted_in_batch}, "
                f"{len(exc.details['writeErrors'])} error(s) — "
                f"first: code={first_err['code']} {first_err['errmsg'][:120]}"
            )

        processed = min(offset + batch_size, len(docs))
        elapsed = time.perf_counter() - start
        rate = processed / elapsed if elapsed > 0 else 0
        print(
            f"[INFO] Progress: {processed}/{len(docs)} "
            f"({processed / len(docs) * 100:.1f}%) | "
            f"{rate:.0f} docs/s"
        )

    elapsed_total = time.perf_counter() - start
    print(
        f"\n[DONE] Import complete in {elapsed_total:.1f}s — "
        f"inserted: {total_inserted}, errors: {total_errors}, "
        f"target: {db_name}.{collection_name}"
    )
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Amap POI JSON data into trip-poi-service MongoDB."
    )
    parser.add_argument("filepath", help="Path to the pois.json file")
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGO_URI", DEFAULT_MONGO_URI),
        help=f"MongoDB URI (env: MONGO_URI, default: {DEFAULT_MONGO_URI})",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"Target database (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Target collection (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Documents per batch insert (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--no-convert",
        action="store_true",
        help=(
            "Skip the Amap→PoiDoc conversion step. "
            "Use this when the input file was already produced by `initializer.convert`."
        ),
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing documents in the collection before importing",
    )
    args = parser.parse_args()

    import_pois(
        filepath=args.filepath,
        mongo_uri=args.uri,
        db_name=args.db,
        collection_name=args.collection,
        batch_size=args.batch_size,
        clear=args.clear,
        no_convert=args.no_convert,
    )


if __name__ == "__main__":
    main()
