"""
Hotel Data Importer Module

This module provides functionality to import Hotel data into MongoDB for the
trip-hotel-service. It mirrors the design of ``initializer.pois`` and supports
the same import modes and CLI interface.

Usage:
    from initializer.hotels import HotelImporter

    importer = HotelImporter(mongo_uri="mongodb://localhost:27017", database="hotel_db")
    importer.import_from_file("path/to/hotels.json", mode=ImportMode.REPLACE)
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Sequence

from bson import Decimal128
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError, PyMongoError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & data classes
# ---------------------------------------------------------------------------


class ImportMode(Enum):
    """
    Import mode enumeration for hotel data import operations.

    - REPLACE:     Drop existing collection and insert all new data.
    - UPSERT:      Update existing documents or insert new ones (by _id).
    - INSERT_ONLY: Only insert new documents, skip existing ones.
    - CLEAR:       Drop the collection without inserting any data.
    """

    REPLACE = "replace"
    UPSERT = "upsert"
    INSERT_ONLY = "insert_only"
    CLEAR = "clear"


@dataclass
class ImportStats:
    """
    Statistics container for import operations.

    Attributes:
        total:        Total number of hotels processed.
        inserted:     Number of newly inserted documents.
        updated:      Number of updated documents.
        skipped:      Number of skipped documents.
        errors:       Number of documents that failed validation / write.
        error_details: List of human-readable error messages.
    """

    total: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"总计: {self.total}, 插入: {self.inserted}, "
            f"更新: {self.updated}, 跳过: {self.skipped}, 错误: {self.errors}"
        )


@dataclass
class HotelImporterConfig:
    """
    Configuration for the hotel importer.

    Attributes:
        mongo_uri:      MongoDB connection URI.
        database:       Database name.
        collection:     Collection name.
        batch_size:     Number of documents to process per batch.
        create_indexes: Whether to create indexes after import.
    """

    mongo_uri: str = "mongodb://root:fudanse@localhost:27017"
    database: str = "hotel_db"
    collection: str = "hotels"
    batch_size: int = 500
    create_indexes: bool = True


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class HotelImporter:
    """
    Hotel data importer for MongoDB.

    Reads hotel documents (conforming to HotelDoc) from JSON files or Python
    objects and writes them into the configured MongoDB collection.

    Example:
        >>> config = HotelImporterConfig(mongo_uri="mongodb://localhost:27017")
        >>> importer = HotelImporter(config)
        >>> stats = importer.import_from_file("hotels.json", mode=ImportMode.UPSERT)
        >>> print(stats)
    """

    def __init__(self, config: HotelImporterConfig | None = None, **kwargs: Any):
        """
        Initialise the hotel importer.

        Args:
            config:   HotelImporterConfig instance. If None, uses defaults.
            **kwargs: Override config values (mongo_uri, database, collection, …).
        """
        if config is None:
            config = HotelImporterConfig()

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

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

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
        """Return the MongoDB collection, connecting lazily if required."""
        if self._collection is None:
            self._connect()
        assert self._collection is not None
        return self._collection

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _create_geospatial_index(self) -> None:
        """Create 2dsphere index on *location* for geospatial queries."""
        logger.info("正在创建地理空间索引…")
        self.collection.create_index([("location", "2dsphere")])
        logger.info("地理空间索引创建完成")

    def _create_text_index(self) -> None:
        """Create text index on *name* for full-text search."""
        logger.info("正在创建文本索引…")
        self.collection.create_index([("name", "text")])
        logger.info("文本索引创建完成")

    def _create_indexes(self) -> None:
        """Create all indexes required by the hotel collection."""
        self._create_geospatial_index()
        self._create_text_index()
        self.collection.create_index("poiId", sparse=True)
        self.collection.create_index("tags", sparse=True)
        logger.info("所有索引创建完成")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_hotel(hotel: dict[str, Any]) -> list[str]:
        """
        Validate a single hotel document.

        Accepts documents with either ``_id`` (preferred) or the legacy ``id``
        field for backwards compatibility.

        Args:
            hotel: Hotel document to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if not hotel.get("_id") and not hotel.get("id"):
            errors.append("缺少必需字段: _id")
        if not hotel.get("name"):
            errors.append("缺少必需字段: name")

        location = hotel.get("location")
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

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """
        Parse a timestamp value into a timezone-aware UTC datetime.

        Accepts ``datetime`` objects and ISO-8601 strings produced by the
        conversion script (e.g. ``"2026-03-06T14:06:57.446Z"``).
        Falls back to *now* when the value is absent or unparseable.
        """
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            cleaned = value.rstrip("Z")
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return datetime.now(timezone.utc)

    @staticmethod
    def _transform_estimated_price(price: Any) -> dict[str, Any] | None:
        """
        Convert the ``estimatedPrice`` sub-document so that ``amount`` is
        stored as BSON ``Decimal128``, which Spring Data maps to
        ``java.math.BigDecimal``.

        Args:
            price: Raw value from the JSON document (dict or None).

        Returns:
            Transformed price dict, or None if the input is absent/invalid.
        """
        if not price or not isinstance(price, dict):
            return None
        amount = price.get("amount")
        currency = price.get("currency", "CNY")
        if amount is None:
            return None
        return {
            "currency": str(currency),
            "amount": Decimal128(str(amount)),
        }

    @staticmethod
    def _transform_hotel(hotel: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a hotel document for MongoDB storage.

        - Renames the legacy ``id`` field to ``_id`` when present.
        - Converts ``createdAt`` / ``updatedAt`` ISO-8601 strings to BSON
          ``Date`` (``datetime``) objects so they match Spring Data's
          ``@CreatedDate`` / ``@LastModifiedDate`` (``Instant``) mapping.
        - Converts ``estimatedPrice.amount`` to BSON ``Decimal128`` so it maps
          correctly to Spring Data's ``BigDecimal`` field.

        Args:
            hotel: Original hotel document.

        Returns:
            Document ready for MongoDB insertion.
        """
        doc = dict(hotel)

        # Backwards-compat: rename 'id' → '_id'
        if "_id" not in doc and "id" in doc:
            doc["_id"] = doc.pop("id")

        # Audit timestamps → BSON Date
        now = datetime.now(timezone.utc)
        doc["createdAt"] = (
            HotelImporter._parse_timestamp(doc.get("createdAt"))
            if doc.get("createdAt")
            else now
        )
        doc["updatedAt"] = (
            HotelImporter._parse_timestamp(doc.get("updatedAt"))
            if doc.get("updatedAt")
            else now
        )

        # estimatedPrice.amount → Decimal128
        doc["estimatedPrice"] = HotelImporter._transform_estimated_price(
            doc.get("estimatedPrice")
        )

        return doc

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def _batch_iterator(
        self, hotels: Sequence[dict[str, Any]]
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield successive batches from *hotels*."""
        for i in range(0, len(hotels), self._batch_size):
            yield list(hotels[i : i + self._batch_size])

    # ------------------------------------------------------------------
    # Import modes
    # ------------------------------------------------------------------

    def _import_clear(self) -> ImportStats:
        """Drop the collection without inserting any data (CLEAR mode)."""
        logger.info("CLEAR 模式: 正在删除集合…")
        self.collection.drop()
        logger.info("集合已清空")
        return ImportStats()

    def _import_replace(self, hotels: Sequence[dict[str, Any]]) -> ImportStats:
        """Drop the existing collection and insert all documents (REPLACE mode)."""
        stats = ImportStats(total=len(hotels))

        logger.info("REPLACE 模式: 正在清空现有数据…")
        self.collection.drop()

        logger.info(f"正在插入 {len(hotels)} 条酒店数据…")

        for batch in self._batch_iterator(hotels):
            docs = []
            for hotel in batch:
                errs = self._validate_hotel(hotel)
                if errs:
                    stats.errors += 1
                    stats.error_details.append(
                        f"Hotel '{hotel.get('name', 'unknown')}': {', '.join(errs)}"
                    )
                    continue
                docs.append(self._transform_hotel(hotel))

            if docs:
                try:
                    result = self.collection.insert_many(docs, ordered=False)
                    stats.inserted += len(result.inserted_ids)
                except BulkWriteError as e:
                    stats.inserted += e.details.get("nInserted", 0)
                    stats.errors += len(e.details.get("writeErrors", []))
                    for err in e.details.get("writeErrors", []):
                        stats.error_details.append(f"批量写入错误: {err.get('errmsg')}")

        return stats

    def _import_upsert(self, hotels: Sequence[dict[str, Any]]) -> ImportStats:
        """Update existing documents or insert new ones (UPSERT mode)."""
        stats = ImportStats(total=len(hotels))

        logger.info(f"UPSERT 模式: 正在处理 {len(hotels)} 条酒店数据…")

        for batch in self._batch_iterator(hotels):
            operations = []
            for hotel in batch:
                errs = self._validate_hotel(hotel)
                if errs:
                    stats.errors += 1
                    stats.error_details.append(
                        f"Hotel '{hotel.get('name', 'unknown')}': {', '.join(errs)}"
                    )
                    continue

                doc = self._transform_hotel(hotel)
                doc_id = doc.pop("_id")
                # Preserve createdAt on subsequent upserts (@CreatedDate semantics)
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
                    for err in details.get("writeErrors", []):
                        stats.error_details.append(f"批量写入错误: {err.get('errmsg')}")

        return stats

    def _import_insert_only(self, hotels: Sequence[dict[str, Any]]) -> ImportStats:
        """Insert only new documents, skipping those that already exist (INSERT_ONLY mode)."""
        stats = ImportStats(total=len(hotels))

        logger.info(f"INSERT_ONLY 模式: 正在处理 {len(hotels)} 条酒店数据…")

        for batch in self._batch_iterator(hotels):
            docs = []
            for hotel in batch:
                errs = self._validate_hotel(hotel)
                if errs:
                    stats.errors += 1
                    stats.error_details.append(
                        f"Hotel '{hotel.get('name', 'unknown')}': {', '.join(errs)}"
                    )
                    continue

                doc = self._transform_hotel(hotel)
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
                    for err in e.details.get("writeErrors", []):
                        if err.get("code") == 11000:  # Duplicate key
                            stats.skipped += 1
                        else:
                            stats.errors += 1
                            stats.error_details.append(
                                f"批量写入错误: {err.get('errmsg')}"
                            )

        return stats

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_data(
        self,
        hotels: Sequence[dict[str, Any]] = (),
        mode: ImportMode = ImportMode.UPSERT,
    ) -> ImportStats:
        """
        Import hotel data into MongoDB.

        For CLEAR mode ``hotels`` is not required and will be ignored.

        Args:
            hotels: Sequence of hotel documents to import.
            mode:   Import mode (REPLACE, UPSERT, INSERT_ONLY, or CLEAR).

        Returns:
            ImportStats with details about the operation.
        """
        logger.info(f"开始操作 (模式: {mode.value})")

        try:
            if mode is ImportMode.CLEAR:
                stats = self._import_clear()
            else:
                logger.info(f"待处理记录数: {len(hotels)}")
                mode_methods = {
                    ImportMode.REPLACE: self._import_replace,
                    ImportMode.UPSERT: self._import_upsert,
                    ImportMode.INSERT_ONLY: self._import_insert_only,
                }
                stats = mode_methods[mode](hotels)

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
        Import hotel data from a JSON file.

        Args:
            file_path: Path to the JSON file containing hotel documents.
            mode:      Import mode. For CLEAR mode the file is not read.
            encoding:  File encoding (default: utf-8).

        Returns:
            ImportStats with details about the operation.

        Raises:
            FileNotFoundError: If the file does not exist (non-CLEAR modes).
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        if mode is ImportMode.CLEAR:
            return self.import_data(mode=mode)

        file_path = Path(file_path)
        logger.info(f"正在读取文件: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding=encoding) as f:
            hotels = json.load(f)

        if not isinstance(hotels, list):
            raise ValueError("JSON 文件必须包含酒店文档数组")

        logger.info(f"已加载 {len(hotels)} 条酒店记录")
        return self.import_data(hotels, mode=mode)

    def get_stats(self) -> dict[str, Any]:
        """
        Return current collection statistics.

        Returns:
            Dict with document count and index names.
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

    def __enter__(self) -> "HotelImporter":
        """Context manager entry — connect on entry."""
        self._connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit — always disconnect."""
        self.close()


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def import_shanghai_hotels(
    mode: ImportMode = ImportMode.UPSERT,
    config: HotelImporterConfig | None = None,
) -> ImportStats:
    """
    Convenience function to import Shanghai hotel data.

    Reads the pre-seeded Shanghai hotel JSON from the standard location in the
    data directory and imports it into MongoDB.

    Args:
        mode:   Import mode (default: UPSERT).
        config: Optional custom configuration.

    Returns:
        ImportStats with details about the operation.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = base_dir / "data" / "seeded" / "shanghai" / "hotels.json"

    with HotelImporter(config) as importer:
        return importer.import_from_file(data_file, mode=mode)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point for command-line execution."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    parser = argparse.ArgumentParser(
        description="酒店数据导入工具 - 将酒店数据导入到 MongoDB"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="酒店 JSON 文件路径 (默认: data/seeded/shanghai/hotels.json)",
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
    parser.add_argument("--database", default="hotel_db", help="数据库名称")
    parser.add_argument("--collection", default="hotels", help="集合名称")
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

    mode_map = {
        "replace": ImportMode.REPLACE,
        "upsert": ImportMode.UPSERT,
        "insert_only": ImportMode.INSERT_ONLY,
        "clear": ImportMode.CLEAR,
    }
    mode = mode_map[args.mode]

    config = HotelImporterConfig(
        mongo_uri=args.uri,
        database=args.database,
        collection=args.collection,
        batch_size=args.batch_size,
        create_indexes=not args.no_indexes,
    )

    print("=" * 60)
    print("酒店数据导入工具")
    print("=" * 60)
    print(f"  数据库: {config.database}")
    print(f"  集合:   {config.collection}")
    print(f"  导入模式: {mode.value}")
    print("=" * 60)

    try:
        with HotelImporter(config) as importer:
            if mode is ImportMode.CLEAR:
                stats = importer.import_data(mode=mode)
            elif args.file:
                stats = importer.import_from_file(args.file, mode=mode)
            else:
                # Default: Shanghai seeded file
                base_dir = Path(__file__).resolve().parent.parent.parent
                data_file = base_dir / "data" / "seeded" / "shanghai" / "hotels.json"
                stats = importer.import_from_file(data_file, mode=mode)

            print("\n" + "=" * 60)
            print("导入完成!")
            print(f"  {stats}")

            if stats.errors > 0:
                print("\n错误详情 (前10条):")
                for error in stats.error_details[:10]:
                    print(f"  - {error}")

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
