"""
Convert raw Amap (AutoNavi) POI records to the PoiDoc schema used by trip-poi-service.

PoiDoc field mapping:
  amapId      <- id
  name        <- name
  location    <- location  ("longitude,latitude" -> GeoJsonPoint)
  address     <- { province: pname, city: cityname, district: adname, detailed: address }
  adcode      <- adcode
  categories  <- type  (split by ";", deduplicated, preserving order)
  images      <- photos[].url

Standalone usage (converts and saves result to a file):
    uv run python -m initializer.convert /path/to/pois.json
    uv run python -m initializer.convert /path/to/pois.json --output /path/to/pois_converted.json
"""

import argparse
import json
from pathlib import Path
from typing import Any


def convert_poi(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a single raw Amap POI record to PoiDoc format."""

    # ── location ──────────────────────────────────────────────────────────────
    # Amap provides "longitude,latitude" as a plain string; MongoDB 2dsphere
    # index requires GeoJSON Point: {"type": "Point", "coordinates": [lon, lat]}
    location: dict[str, Any] | None = None
    raw_location = raw.get("location", "")
    if raw_location:
        try:
            lon_str, lat_str = raw_location.split(",")
            location = {
                "type": "Point",
                "coordinates": [float(lon_str.strip()), float(lat_str.strip())],
            }
        except (ValueError, AttributeError):
            pass

    # ── address ───────────────────────────────────────────────────────────────
    address = {
        "province": (raw.get("pname") or "").strip(),
        "city": (raw.get("cityname") or "").strip(),
        "district": (raw.get("adname") or "").strip(),
        "detailed": (raw.get("address") or "").strip(),
    }

    # ── categories ────────────────────────────────────────────────────────────
    # e.g. "科教文化服务;会展中心;会展中心" -> ["科教文化服务", "会展中心"]
    raw_type = raw.get("type", "")
    # dict.fromkeys preserves insertion order while deduplicating
    categories: list[str] = list(
        dict.fromkeys(c.strip() for c in raw_type.split(";") if c.strip())
    )

    # ── images ────────────────────────────────────────────────────────────────
    photos = raw.get("photos") or []
    images: list[str] = [
        p["url"] for p in photos if isinstance(p, dict) and p.get("url")
    ]

    return {
        "name": (raw.get("name") or "").strip(),
        "location": location,
        "address": address,
        "adcode": (raw.get("adcode") or "").strip(),
        "amapId": (raw.get("id") or "").strip(),
        "categories": categories,
        "images": images,
    }


def convert_all(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert a list of raw Amap POI records.

    Records that are missing a name or a parseable location are skipped,
    as they cannot satisfy the 2dsphere index requirement.
    """
    result: list[dict[str, Any]] = []
    skipped = 0
    for raw in raw_list:
        try:
            doc = convert_poi(raw)
            if not doc["name"] or doc["location"] is None:
                skipped += 1
                continue
            result.append(doc)
        except Exception as exc:
            skipped += 1
            print(f"[WARN] Skipping record id={raw.get('id', '?')}: {exc}")
    if skipped:
        print(f"[INFO] Skipped {skipped} records (missing name or location).")
    return result


def load_and_convert(filepath: str) -> list[dict[str, Any]]:
    """Load a raw pois.json file and return a list of converted PoiDoc-compatible dicts."""
    print(f"[INFO] Reading {filepath} ...")
    with open(filepath, encoding="utf-8") as f:
        raw_list: list[dict[str, Any]] = json.load(f)
    print(f"[INFO] Loaded {len(raw_list)} raw records.")
    converted = convert_all(raw_list)
    print(f"[INFO] Converted {len(converted)} valid records.")
    return converted


def save_converted(docs: list[dict[str, Any]], output_path: str) -> None:
    """
    Persist converted PoiDoc-compatible dicts to a JSON file.

    The file uses compact encoding (no indentation) with ensure_ascii=False
    so that Chinese characters are stored as-is rather than as \\uXXXX escapes,
    keeping the file size reasonable for hundreds-of-thousands of records.
    """
    print(f"[INFO] Writing {len(docs)} converted records to {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = Path(output_path).stat().st_size / 1024 / 1024
    print(f"[INFO] Saved → {output_path} ({size_mb:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert raw Amap POI JSON to PoiDoc format and save to a file."
    )
    parser.add_argument("filepath", help="Path to the raw pois.json from Amap")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Output file path for converted data. "
            "Defaults to <input_stem>_converted.json in the same directory."
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.filepath)
    output_path = (
        args.output
        if args.output
        else str(input_path.parent / f"{input_path.stem}_converted.json")
    )

    docs = load_and_convert(args.filepath)
    if not docs:
        print("[WARN] No valid records to save.")
        return
    save_converted(docs, output_path)


if __name__ == "__main__":
    main()
