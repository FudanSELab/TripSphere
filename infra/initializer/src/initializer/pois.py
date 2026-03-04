"""
Import / export POI data for the trip-poi-service MongoDB collection.

File naming convention
----------------------
  amap_pois.json         Raw POI data scraped from Amap (original source)
  pois_converted.json    Cleaned PoiDoc format, no _id (intermediate)
  pois.json              Canonical version with stable _id values (source of truth)

Subcommands
-----------

import
    Import POI documents into MongoDB.  Three input flavours are supported:

    a) Raw Amap JSON (default conversion):
           uv run -m initializer.pois import data/amap_pois.json

    b) Pre-converted PoiDoc JSON (--no-convert):
           uv run -m initializer.pois import data/pois_converted.json --no-convert

    c) Canonical pois.json with ``_id`` (--no-convert, recommended):
       ``_id`` strings are automatically converted to bson.ObjectId so the
       exact same IDs are restored in MongoDB.
           uv run -m initializer.pois import data/pois.json --no-convert

export
    Dump poi_db.pois to a JSON file, serialising ObjectId ``_id`` as 24-char
    hex strings.  The output (default: data/pois.json) becomes the canonical
    source-of-truth: re-importing it always restores identical IDs, so other
    seed files (hotels.json) can safely hardcode ``poiId`` references.

        uv run -m initializer.pois export
        uv run -m initializer.pois export --output data/pois.json

Options shared by both subcommands:
    --uri         MongoDB connection URI  (default: mongodb://root:fudanse@localhost:27017)
    --db          Database name          (default: poi_db)
    --collection  Collection name        (default: pois)
"""

import argparse
import json
import os
import time
from pathlib import Path

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from initializer.convert import load_and_convert

# ── Defaults (match trip-poi-service application.yaml) ─────────────────────
DEFAULT_MONGO_URI = "mongodb://root:fudanse@localhost:27017"
DEFAULT_DB = "poi_db"
DEFAULT_COLLECTION = "pois"
DEFAULT_BATCH_SIZE = 1000


def load_converted(filepath: str) -> list[dict]:
    """
    Load a pre-converted PoiDoc JSON file.

    If the documents contain an ``_id`` field (i.e. the file was produced by
    ``export_pois``), each ``_id`` string is converted back to
    ``bson.ObjectId`` so MongoDB restores the exact same IDs on re-import.
    """
    print(f"[INFO] Loading pre-converted data from {filepath} ...")
    with open(filepath, encoding="utf-8") as f:
        docs: list[dict] = json.load(f)
    print(f"[INFO] Loaded {len(docs)} records.")

    # Detect whether this is a seeded dump (contains _id fields)
    if docs and "_id" in docs[0]:
        for doc in docs:
            raw_id = doc.get("_id")
            if isinstance(raw_id, str):
                doc["_id"] = ObjectId(raw_id)
        print(
            f"[INFO] Detected seeded dump — converted {len(docs)} _id strings to ObjectId."
        )

    return docs


def export_pois(
    output_path: str,
    mongo_uri: str = DEFAULT_MONGO_URI,
    db_name: str = DEFAULT_DB,
    collection_name: str = DEFAULT_COLLECTION,
) -> None:
    """
    Dump poi_db.pois to a JSON file with ``_id`` serialised as hex strings.

    The resulting file can be re-imported via ``import_pois(..., no_convert=True)``
    to restore the exact same ObjectId values, making cross-deployment
    references (e.g. hotels.json → poiId) stable.
    """
    print(f"[INFO] Connecting to MongoDB at {mongo_uri} ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")

    collection = client[db_name][collection_name]
    total = collection.count_documents({})
    print(f"[INFO] Exporting {total} documents from {db_name}.{collection_name} ...")

    docs = []
    for doc in collection.find({}):
        doc["_id"] = str(doc["_id"])  # ObjectId → 24-char hex string
        docs.append(doc)

    client.close()

    print(f"[INFO] Writing to {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, separators=(",", ":"), indent=4)

    size_mb = Path(output_path).stat().st_size / 1024 / 1024
    print(f"[DONE] Exported {len(docs)} documents → {output_path} ({size_mb:.1f} MB)")


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


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Attach --uri / --db / --collection to a (sub)parser."""
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGO_URI", DEFAULT_MONGO_URI),
        help=f"MongoDB URI (env: MONGO_URI, default: {DEFAULT_MONGO_URI})",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"Database name (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Collection name (default: {DEFAULT_COLLECTION})",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import / export POI data for trip-poi-service MongoDB."
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── import subcommand ────────────────────────────────────────────────────
    import_parser = subparsers.add_parser(
        "import", help="Import POI JSON into MongoDB."
    )
    import_parser.add_argument(
        "filepath",
        help=(
            "Input file. Accepts: raw pois.json, pois_converted.json (--no-convert), "
            "or pois.json with _id (--no-convert, IDs restored automatically)."
        ),
    )
    _add_common_args(import_parser)
    import_parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Documents per batch insert (default: {DEFAULT_BATCH_SIZE})",
    )
    import_parser.add_argument(
        "--no-convert",
        action="store_true",
        help="Skip Amap→PoiDoc conversion; input is already in PoiDoc format.",
    )
    import_parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing documents before importing.",
    )

    # ── export subcommand ────────────────────────────────────────────────────
    export_parser = subparsers.add_parser(
        "export",
        help="Export poi_db.pois to a JSON file with _id preserved as hex strings.",
    )
    _add_common_args(export_parser)
    export_parser.add_argument(
        "--output",
        default="data/pois.json",
        help="Output file path (default: data/pois.json)",
    )

    args = parser.parse_args()

    if args.command == "export":
        export_pois(
            output_path=args.output,
            mongo_uri=args.uri,
            db_name=args.db,
            collection_name=args.collection,
        )
    elif args.command == "import":
        import_pois(
            filepath=args.filepath,
            mongo_uri=args.uri,
            db_name=args.db,
            collection_name=args.collection,
            batch_size=args.batch_size,
            clear=args.clear,
            no_convert=args.no_convert,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
