"""
POI Data Importer Module

This module provides functionality to import POI (Point of Interest) data
into MongoDB for the trip-poi-service. It supports multiple import modes
and ensures data integrity with proper error handling.

Usage:
    from initializer.pois import PoiImporter

    importer = PoiImporter(mongo_uri="mongodb://localhost:27017", database="poi_db")
    importer.import_from_file("path/to/pois.json", mode=ImportMode.REPLACE)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError, PyMongoError

from initializer.config.settings import get_settings
from initializer.types import ImportMode, ImportStats

logger = logging.getLogger(__name__)


@dataclass
class PoiImporterConfig:
    """
    Configuration for POI importer.

    Attributes:
        mongo_uri: MongoDB connection URI (defaults to Settings.mongo.uri)
        database: Database name
        collection: Collection name
        batch_size: Number of documents to process in each batch
            (defaults to Settings.importer.batch_size)
        create_indexes: Whether to create indexes after import
            (defaults to Settings.importer.create_indexes)
    """

    mongo_uri: str = field(default_factory=lambda: get_settings().mongo.uri)
    database: str = "poi_db"
    collection: str = "pois"
    batch_size: int = field(default_factory=lambda: get_settings().importer.batch_size)
    create_indexes: bool = field(
        default_factory=lambda: get_settings().importer.create_indexes
    )


class PoiImporter:
    """
    POI data importer for MongoDB.

    This class handles the import of POI data from JSON files or Python objects
    into MongoDB. It supports multiple import modes and provides detailed
    statistics about the import process.

    Example:
        >>> config = PoiImporterConfig(mongo_uri="mongodb://localhost:27017")
        >>> importer = PoiImporter(config)
        >>> stats = importer.import_from_file("pois.json", mode=ImportMode.UPSERT)
        >>> print(stats)
    """

    def __init__(self, config: PoiImporterConfig | None = None, **kwargs: Any):
        """
        Initialize the POI importer.

        Args:
            config: PoiImporterConfig instance. If None, uses default config.
            **kwargs: Override config values (mongo_uri, database, collection, etc.)
        """
        if config is None:
            config = PoiImporterConfig()

        # Allow kwargs to override config values
        self._mongo_uri = kwargs.get("mongo_uri", config.mongo_uri)
        self._database_name = kwargs.get("database", config.database)
        self._collection_name = kwargs.get("collection", config.collection)
        self._batch_size = kwargs.get("batch_size", config.batch_size)
        self._should_create_indexes = kwargs.get(
            "create_indexes", config.create_indexes
        )

        self._client: MongoClient | None = None
        self._db: Database | None = None
        self._collection: Collection | None = None

    def _connect(self) -> None:
        """Establish MongoDB connection."""
        if self._client is None:
            logger.info(f"正在连接 MongoDB: {self._mongo_uri}")
            self._client = MongoClient(self._mongo_uri)
            self._db = self._client[self._database_name]
            self._collection = self._db[self._collection_name]
            logger.info(
                f"已连接到数据库: {self._database_name}.{self._collection_name}"
            )

    def _disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None
            logger.info("已断开 MongoDB 连接")

    @property
    def collection(self) -> Collection:
        """Get the MongoDB collection, connecting if necessary."""
        if self._collection is None:
            self._connect()
        assert self._collection is not None
        return self._collection

    def _create_geospatial_index(self) -> None:
        """Create 2dsphere index on location field for geospatial queries."""
        logger.info("正在创建地理空间索引...")
        self.collection.create_index([("location", "2dsphere")])
        logger.info("地理空间索引创建完成")

    def _create_text_index(self) -> None:
        """Create text index on name field for text search."""
        logger.info("正在创建文本索引...")
        self.collection.create_index([("name", "text")])
        logger.info("文本索引创建完成")

    def _create_indexes(self) -> None:
        """Create all necessary indexes for the POI collection."""
        self._create_geospatial_index()
        self._create_text_index()
        # Create additional indexes for common query patterns
        self.collection.create_index("amapId", sparse=True)
        self.collection.create_index("adcode", sparse=True)
        self.collection.create_index("categories", sparse=True)
        logger.info("所有索引创建完成")

    @staticmethod
    def _validate_poi(poi: dict[str, Any]) -> list[str]:
        """
        Validate a single POI document.

        Accepts documents with either '_id' (preferred, native MongoDB format)
        or the legacy 'id' field for backwards compatibility.

        Args:
            poi: POI document to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Accept '_id' (preferred) or legacy 'id' field.
        if not poi.get("_id") and not poi.get("id"):
            errors.append("缺少必需字段: _id")
        if not poi.get("name"):
            errors.append("缺少必需字段: name")

        # Validate the location field.
        location = poi.get("location")
        if not location:
            errors.append("缺少必需字段: location")
        elif not isinstance(location, dict):
            errors.append("location 必须是对象类型")
        else:
            if location.get("type") != "Point":
                errors.append("location.type 必须是 'Point'")
            coords = location.get("coordinates")
            if not coords or len(coords) != 2:
                errors.append("location.coordinates 必须包含 [lng, lat]")
            elif not all(isinstance(c, (int, float)) for c in coords):
                errors.append("location.coordinates 必须是数值类型")

        return errors

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """
        Parse a timestamp value into a timezone-aware datetime (UTC).

        Accepts:
        - ``datetime`` objects (made UTC-aware if naive)
        - ISO-8601 strings produced by the enrichment script
          (e.g. ``"2026-03-06T07:00:00.000Z"``)

        Falls back to *now* when the value is missing or unparseable so that
        every document always carries valid audit timestamps.
        """
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            # Strip trailing 'Z', parse the timestamp, and attach UTC tzinfo.
            cleaned = value.rstrip("Z")
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return datetime.now(timezone.utc)

    @staticmethod
    def _transform_poi(poi: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a POI document for MongoDB storage.

        - Renames the legacy ``id`` field to ``_id`` when present.
        - Converts the ISO-8601 string timestamps ``createdAt`` / ``updatedAt``
          to timezone-aware ``datetime`` objects so that pymongo stores them as
          proper BSON Date values (matching Spring Data's ``Instant`` mapping).
        - Inserts ``createdAt`` / ``updatedAt`` with *now* when absent, so that
          manually crafted documents are also consistent.

        Args:
            poi: Original POI document

        Returns:
            Document ready for MongoDB insertion
        """
        doc = dict(poi)

        # Backward compatibility: rename 'id' -> '_id'.
        if "_id" not in doc and "id" in doc:
            doc["_id"] = doc.pop("id")

        # Ensure audit timestamps are stored as BSON-compatible datetime objects.
        now = datetime.now(timezone.utc)
        doc["createdAt"] = (
            PoiImporter._parse_timestamp(doc.get("createdAt"))
            if doc.get("createdAt")
            else now
        )
        doc["updatedAt"] = (
            PoiImporter._parse_timestamp(doc.get("updatedAt"))
            if doc.get("updatedAt")
            else now
        )

        return doc

    def _batch_iterator(
        self, pois: Sequence[dict[str, Any]]
    ) -> Iterator[list[dict[str, Any]]]:
        """
        Yield batches of POIs for bulk operations.

        Args:
            pois: Sequence of POI documents

        Yields:
            Batches of POI documents
        """
        for i in range(0, len(pois), self._batch_size):
            yield list(pois[i : i + self._batch_size])

    def _import_clear(self) -> ImportStats:
        """
        Clear the collection without inserting any data (CLEAR mode).

        Drops the entire collection, which also removes all indexes.
        Indexes will be recreated afterwards if ``create_indexes`` is enabled.

        Returns:
            ImportStats with total=0 and no insertions
        """
        logger.info("CLEAR 模式: 正在删除集合...")
        self.collection.drop()
        logger.info("集合已清空")
        return ImportStats()

    def _import_replace(self, pois: Sequence[dict[str, Any]]) -> ImportStats:
        """
        Import POIs using REPLACE mode (drop and insert).

        Args:
            pois: Sequence of POI documents

        Returns:
            Import statistics
        """
        stats = ImportStats(total=len(pois))

        logger.info("REPLACE 模式: 正在清空现有数据...")
        self.collection.drop()

        logger.info(f"正在插入 {len(pois)} 条 POI 数据...")

        for batch in self._batch_iterator(pois):
            docs = []
            for poi in batch:
                validation_errors = self._validate_poi(poi)
                if validation_errors:
                    stats.errors += 1
                    name = poi.get("name", "unknown")
                    stats.error_details.append(
                        f"POI '{name}': {', '.join(validation_errors)}"
                    )
                    continue
                docs.append(self._transform_poi(poi))

            if docs:
                try:
                    result = self.collection.insert_many(docs, ordered=False)
                    stats.inserted += len(result.inserted_ids)
                except BulkWriteError as e:
                    stats.inserted += e.details.get("nInserted", 0)
                    stats.errors += len(e.details.get("writeErrors", []))
                    for error in e.details.get("writeErrors", []):
                        stats.error_details.append(
                            f"批量写入错误: {error.get('errmsg')}"
                        )

        return stats

    def _import_upsert(self, pois: Sequence[dict[str, Any]]) -> ImportStats:
        """
        Import POIs using UPSERT mode (update or insert).

        Args:
            pois: Sequence of POI documents

        Returns:
            Import statistics
        """
        stats = ImportStats(total=len(pois))

        logger.info(f"UPSERT 模式: 正在处理 {len(pois)} 条 POI 数据...")

        for batch in self._batch_iterator(pois):
            operations = []
            for poi in batch:
                validation_errors = self._validate_poi(poi)
                if validation_errors:
                    stats.errors += 1
                    name = poi.get("name", "unknown")
                    stats.error_details.append(
                        f"POI '{name}': {', '.join(validation_errors)}"
                    )
                    continue

                doc = self._transform_poi(poi)
                doc_id = doc.pop("_id")
                # 'createdAt' must not be overwritten on subsequent upserts —
                # use $setOnInsert so it is written only when the document is
                # first created, mirroring @CreatedDate semantics.
                created_at = doc.pop("createdAt")
                doc["updatedAt"] = datetime.now(timezone.utc)
                operations.append(
                    UpdateOne(
                        {"_id": doc_id},
                        {
                            "$set": doc,
                            "$setOnInsert": {"createdAt": created_at},
                        },
                        upsert=True,
                    )
                )

            if operations:
                try:
                    result = self.collection.bulk_write(operations, ordered=False)
                    stats.inserted += result.upserted_count
                    stats.updated += result.modified_count
                except BulkWriteError as e:
                    details = e.details
                    stats.inserted += details.get("nUpserted", 0)
                    stats.updated += details.get("nModified", 0)
                    stats.errors += len(details.get("writeErrors", []))
                    for error in details.get("writeErrors", []):
                        stats.error_details.append(
                            f"批量写入错误: {error.get('errmsg')}"
                        )

        return stats

    def _import_insert_only(self, pois: Sequence[dict[str, Any]]) -> ImportStats:
        """
        Import POIs using INSERT_ONLY mode (skip existing).

        Args:
            pois: Sequence of POI documents

        Returns:
            Import statistics
        """
        stats = ImportStats(total=len(pois))

        logger.info(f"INSERT_ONLY 模式: 正在处理 {len(pois)} 条 POI 数据...")

        for batch in self._batch_iterator(pois):
            docs = []
            for poi in batch:
                validation_errors = self._validate_poi(poi)
                if validation_errors:
                    stats.errors += 1
                    name = poi.get("name", "unknown")
                    stats.error_details.append(
                        f"POI '{name}': {', '.join(validation_errors)}"
                    )
                    continue

                doc = self._transform_poi(poi)
                # Check if document already exists
                if self.collection.find_one({"_id": doc["_id"]}, {"_id": 1}):
                    stats.skipped += 1
                    continue
                docs.append(doc)

            if docs:
                try:
                    result = self.collection.insert_many(docs, ordered=False)
                    stats.inserted += len(result.inserted_ids)
                except BulkWriteError as e:
                    stats.inserted += e.details.get("nInserted", 0)
                    # Duplicate key errors are expected, count as skipped
                    for error in e.details.get("writeErrors", []):
                        if error.get("code") == 11000:  # Duplicate key
                            stats.skipped += 1
                        else:
                            stats.errors += 1
                            stats.error_details.append(
                                f"批量写入错误: {error.get('errmsg')}"
                            )

        return stats

    def import_data(
        self,
        pois: Sequence[dict[str, Any]] = (),
        mode: ImportMode = ImportMode.UPSERT,
    ) -> ImportStats:
        """
        Import POI data into MongoDB.

        For CLEAR mode, ``pois`` is not required and will be ignored.

        Args:
            pois: Sequence of POI documents to import (ignored for CLEAR mode)
            mode: Import mode (REPLACE, UPSERT, INSERT_ONLY, or CLEAR)

        Returns:
            ImportStats with details about the operation
        """
        logger.info(f"开始操作 (模式: {mode.value})")

        try:
            if mode is ImportMode.CLEAR:
                stats = self._import_clear()
            else:
                logger.info(f"待处理记录数: {len(pois)}")
                data_methods = {
                    ImportMode.REPLACE: self._import_replace,
                    ImportMode.UPSERT: self._import_upsert,
                    ImportMode.INSERT_ONLY: self._import_insert_only,
                }
                stats = data_methods[mode](pois)

            # Create indexes after the operation if configured.
            # For CLEAR mode this recreates indexes on an empty collection so
            # the service still starts with a consistent schema.
            if self._should_create_indexes:
                self._create_indexes()

            logger.info(f"操作完成: {stats}")
            return stats

        except PyMongoError as e:
            logger.error(f"MongoDB 操作失败: {e}")
            raise

    def import_from_file(
        self,
        file_path: str | Path,
        mode: ImportMode = ImportMode.UPSERT,
        encoding: str = "utf-8",
    ) -> ImportStats:
        """
        Import POI data from a JSON file.

        Args:
            file_path: Path to the JSON file containing POI data
            mode: Import mode (REPLACE, UPSERT, INSERT_ONLY, or CLEAR).
                  For CLEAR mode the file is not read; pass any valid path.
            encoding: File encoding (default: utf-8)

        Returns:
            ImportStats with details about the operation

        Raises:
            FileNotFoundError: If the file does not exist (non-CLEAR modes)
            json.JSONDecodeError: If the file contains invalid JSON
        """
        # CLEAR mode does not require reading any file.
        if mode is ImportMode.CLEAR:
            return self.import_data(mode=mode)

        file_path = Path(file_path)
        logger.info(f"正在读取文件: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding=encoding) as f:
            pois = json.load(f)

        if not isinstance(pois, list):
            raise ValueError("JSON 文件必须包含 POI 数组")

        logger.info(f"已加载 {len(pois)} 条 POI 记录")
        return self.import_data(pois, mode=mode)

    def get_stats(self) -> dict[str, Any]:
        """
        Get current collection statistics.

        Returns:
            Dictionary containing collection stats
        """
        count = self.collection.count_documents({})
        indexes = list(self.collection.list_indexes())
        return {
            "database": self._database_name,
            "collection": self._collection_name,
            "document_count": count,
            "indexes": [idx["name"] for idx in indexes],
        }

    def close(self) -> None:
        """Close the MongoDB connection."""
        self._disconnect()

    def __enter__(self) -> "PoiImporter":
        """Context manager entry."""
        self._connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


def import_shanghai_pois(
    mode: ImportMode = ImportMode.UPSERT,
    config: PoiImporterConfig | None = None,
) -> ImportStats:
    """
    Convenience function to import Shanghai POI data.

    This function imports the pre-seeded Shanghai POI data from the
    standard location in the data directory.

    Args:
        mode: Import mode (default: UPSERT)
        config: Optional custom configuration

    Returns:
        ImportStats with details about the operation
    """
    # Determine data file path
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = base_dir / "data" / "seeded" / "shanghai" / "pois.json"

    with PoiImporter(config) as importer:
        return importer.import_from_file(data_file, mode=mode)


def main() -> None:
    """
    Main entry point for command-line execution.
    """
    import argparse
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    parser = argparse.ArgumentParser(
        description="POI 数据导入工具 - 将 POI 数据导入到 MongoDB"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="POI JSON 文件路径 (默认: data/seeded/shanghai/pois.json)",
    )
    parser.add_argument(
        "--mode",
        choices=["replace", "upsert", "insert_only", "clear"],
        default="upsert",
        help=(
            "操作模式: replace(替换), upsert(更新或插入), "
            "insert_only(仅插入新数据), clear(仅清空集合)"
        ),
    )
    parser.add_argument(
        "--uri",
        default="mongodb://root:fudanse@localhost:27017",
        help="MongoDB 连接 URI",
    )
    parser.add_argument("--database", default="poi_db", help="数据库名称")
    parser.add_argument("--collection", default="pois", help="集合名称")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="批量操作大小",
    )
    parser.add_argument(
        "--no-indexes",
        action="store_true",
        help="跳过索引创建",
    )

    args = parser.parse_args()

    # Determine import mode
    mode_map = {
        "replace": ImportMode.REPLACE,
        "upsert": ImportMode.UPSERT,
        "insert_only": ImportMode.INSERT_ONLY,
        "clear": ImportMode.CLEAR,
    }
    mode = mode_map[args.mode]

    # Create configuration
    config = PoiImporterConfig(
        mongo_uri=args.uri,
        database=args.database,
        collection=args.collection,
        batch_size=args.batch_size,
        create_indexes=not args.no_indexes,
    )

    print("=" * 60)
    print("POI 数据导入工具")
    print("=" * 60)
    print(f"  数据库: {config.database}")
    print(f"  集合: {config.collection}")
    print(f"  导入模式: {mode.value}")
    print("=" * 60)

    try:
        with PoiImporter(config) as importer:
            if mode is ImportMode.CLEAR:
                # CLEAR mode does not require a data file.
                stats = importer.import_data(mode=mode)
            elif args.file:
                stats = importer.import_from_file(args.file, mode=mode)
            else:
                # Use the default Shanghai POI file.
                base_dir = Path(__file__).resolve().parent.parent.parent
                data_file = base_dir / "data" / "seeded" / "shanghai" / "pois.json"
                stats = importer.import_from_file(data_file, mode=mode)

            # Print results.
            print("\n" + "=" * 60)
            print("导入完成!")
            print(f"  {stats}")

            if stats.errors > 0:
                print("\n错误详情 (前10条):")
                for error in stats.error_details[:10]:
                    print(f"  - {error}")

            # Print collection statistics.
            collection_stats = importer.get_stats()
            print("\n集合统计:")
            print(f"  文档总数: {collection_stats['document_count']}")
            print(f"  索引: {', '.join(collection_stats['indexes'])}")
            print("=" * 60)

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except PyMongoError as e:
        print(f"数据库错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
