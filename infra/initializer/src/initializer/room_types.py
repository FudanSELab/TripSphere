"""
Room Type Data Importer Module

This module provides functionality to import RoomType data into MongoDB.

Usage:
    from initializer.room_types import RoomTypeImporter

    importer = RoomTypeImporter(mongo_uri="mongodb://localhost:27017", database="hotel_db")
    importer.import_from_file("path/to/room_types.json", mode=ImportMode.REPLACE)
"""  # noqa: E501

import json
import logging
import sys
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


# ---------------------------------------------------------------------------
# Importer config
# ---------------------------------------------------------------------------


@dataclass
class RoomTypeImporterConfig:
    """
    Configuration for the room type importer.

    Attributes:
        mongo_uri:      MongoDB connection URI (defaults to Settings.mongo.uri).
        database:       Database name.
        collection:     Collection name.
        batch_size:     Number of documents to process per batch
                        (defaults to Settings.importer.batch_size).
        create_indexes: Whether to create indexes after import
                        (defaults to Settings.importer.create_indexes).
    """

    mongo_uri: str = field(default_factory=lambda: get_settings().mongo.uri)
    database: str = "hotel_db"
    collection: str = "room_types"
    batch_size: int = field(default_factory=lambda: get_settings().importer.batch_size)
    create_indexes: bool = field(
        default_factory=lambda: get_settings().importer.create_indexes
    )


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class RoomTypeImporter:
    """
    Room type data importer for MongoDB.

    Reads room type documents (conforming to RoomTypeDoc) from JSON files or
    Python objects and writes them into the configured MongoDB collection.

    Example:
        >>> config = RoomTypeImporterConfig(mongo_uri="mongodb://localhost:27017")
        >>> importer = RoomTypeImporter(config)
        >>> stats = importer.import_from_file("room_types.json", mode=ImportMode.UPSERT)
        >>> print(stats)
    """

    def __init__(self, config: RoomTypeImporterConfig | None = None, **kwargs: Any):
        """
        Initialise the room type importer.

        Args:
            config:   RoomTypeImporterConfig instance. If None, uses defaults.
            **kwargs: Override config values (mongo_uri, database, collection, …).
        """
        if config is None:
            config = RoomTypeImporterConfig()

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

    def _create_indexes(self) -> None:
        """Create all indexes required by the room_types collection."""
        logger.info("正在创建索引…")
        # Primary lookup: fetch all room types for a given hotel
        self.collection.create_index("hotelId")
        # Sparse name index to support text search within a hotel's room types
        self.collection.create_index([("name", "text")], sparse=True)
        logger.info("所有索引创建完成")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_room_type(room_type: dict[str, Any]) -> list[str]:
        """
        Validate a single room type document.

        Accepts documents with either ``_id`` (preferred) or the legacy ``id``
        field for backwards compatibility.

        Args:
            room_type: RoomType document to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if not room_type.get("_id") and not room_type.get("id"):
            errors.append("缺少必需字段: _id")
        if not room_type.get("hotelId"):
            errors.append("缺少必需字段: hotelId")
        if not room_type.get("name"):
            errors.append("缺少必需字段: name")

        return errors

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """
        Parse a timestamp value into a timezone-aware UTC datetime.

        Accepts ``datetime`` objects and ISO-8601 strings produced by the
        creation script (e.g. ``"2026-03-09T07:35:26.723Z"``).
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
    def _transform_room_type(room_type: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a room type document for MongoDB storage.

        - Renames the legacy ``id`` field to ``_id`` when present.
        - Converts ``createdAt`` / ``updatedAt`` ISO-8601 strings to BSON
          ``Date`` (``datetime``) objects so they match Spring Data's
          ``@CreatedDate`` / ``@LastModifiedDate`` (``Instant``) mapping.

        Args:
            room_type: Original room type document.

        Returns:
            Document ready for MongoDB insertion.
        """
        doc = dict(room_type)

        # Backward compatibility: rename 'id' -> '_id'
        if "_id" not in doc and "id" in doc:
            doc["_id"] = doc.pop("id")

        # Convert audit timestamps to BSON Date values.
        now = datetime.now(timezone.utc)
        doc["createdAt"] = (
            RoomTypeImporter._parse_timestamp(doc.get("createdAt"))
            if doc.get("createdAt")
            else now
        )
        doc["updatedAt"] = (
            RoomTypeImporter._parse_timestamp(doc.get("updatedAt"))
            if doc.get("updatedAt")
            else now
        )

        return doc

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def _batch_iterator(
        self, room_types: Sequence[dict[str, Any]]
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield successive batches from *room_types*."""
        for i in range(0, len(room_types), self._batch_size):
            yield list(room_types[i : i + self._batch_size])

    # ------------------------------------------------------------------
    # Import modes
    # ------------------------------------------------------------------

    def _import_clear(self) -> ImportStats:
        """Drop the collection without inserting any data (CLEAR mode)."""
        logger.info("CLEAR 模式: 正在删除集合…")
        self.collection.drop()
        logger.info("集合已清空")
        return ImportStats()

    def _import_replace(self, room_types: Sequence[dict[str, Any]]) -> ImportStats:
        """Drop the existing collection and insert all documents (REPLACE mode)."""
        stats = ImportStats(total=len(room_types))

        logger.info("REPLACE 模式: 正在清空现有数据…")
        self.collection.drop()

        logger.info(f"正在插入 {len(room_types)} 条房型数据…")

        for batch in self._batch_iterator(room_types):
            docs = []
            for room_type in batch:
                errs = self._validate_room_type(room_type)
                if errs:
                    stats.errors += 1
                    name = room_type.get("name", "unknown")
                    stats.error_details.append(f"RoomType '{name}': {', '.join(errs)}")
                    continue
                docs.append(self._transform_room_type(room_type))

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

    def _import_upsert(self, room_types: Sequence[dict[str, Any]]) -> ImportStats:
        """Update existing documents or insert new ones (UPSERT mode)."""
        stats = ImportStats(total=len(room_types))

        logger.info(f"UPSERT 模式: 正在处理 {len(room_types)} 条房型数据…")

        for batch in self._batch_iterator(room_types):
            operations = []
            for room_type in batch:
                errs = self._validate_room_type(room_type)
                if errs:
                    stats.errors += 1
                    name = room_type.get("name", "unknown")
                    stats.error_details.append(f"RoomType '{name}': {', '.join(errs)}")
                    continue

                doc = self._transform_room_type(room_type)
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

    def _import_insert_only(self, room_types: Sequence[dict[str, Any]]) -> ImportStats:
        """Insert only new documents,
        skipping those that already exist (INSERT_ONLY mode).
        """
        stats = ImportStats(total=len(room_types))

        logger.info(f"INSERT_ONLY 模式: 正在处理 {len(room_types)} 条房型数据…")

        for batch in self._batch_iterator(room_types):
            docs = []
            for room_type in batch:
                errs = self._validate_room_type(room_type)
                if errs:
                    stats.errors += 1
                    name = room_type.get("name", "unknown")
                    stats.error_details.append(f"RoomType '{name}': {', '.join(errs)}")
                    continue

                doc = self._transform_room_type(room_type)
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
        room_types: Sequence[dict[str, Any]] = (),
        mode: ImportMode = ImportMode.UPSERT,
    ) -> ImportStats:
        """
        Import room type data into MongoDB.

        For CLEAR mode ``room_types`` is not required and will be ignored.

        Args:
            room_types: Sequence of room type documents to import.
            mode:       Import mode (REPLACE, UPSERT, INSERT_ONLY, or CLEAR).

        Returns:
            ImportStats with details about the operation.
        """
        logger.info(f"开始操作 (模式: {mode.value})")

        try:
            if mode is ImportMode.CLEAR:
                stats = self._import_clear()
            else:
                logger.info(f"待处理记录数: {len(room_types)}")
                mode_methods = {
                    ImportMode.REPLACE: self._import_replace,
                    ImportMode.UPSERT: self._import_upsert,
                    ImportMode.INSERT_ONLY: self._import_insert_only,
                }
                stats = mode_methods[mode](room_types)

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
        Import room type data from a JSON file.

        Args:
            file_path: Path to the JSON file containing room type documents.
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
            room_types = json.load(f)

        if not isinstance(room_types, list):
            raise ValueError("JSON 文件必须包含房型文档数组")

        logger.info(f"已加载 {len(room_types)} 条房型记录")
        return self.import_data(room_types, mode=mode)

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

    def __enter__(self) -> "RoomTypeImporter":
        """Context manager entry — connect on entry."""
        self._connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit — always disconnect."""
        self.close()


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def import_shanghai_room_types(
    mode: ImportMode = ImportMode.UPSERT,
    config: RoomTypeImporterConfig | None = None,
) -> ImportStats:
    """
    Convenience function to import Shanghai room type data.

    Reads the pre-seeded Shanghai room type JSON from the standard location in
    the data directory and imports it into MongoDB.

    Args:
        mode:   Import mode (default: UPSERT).
        config: Optional custom configuration.

    Returns:
        ImportStats with details about the operation.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = base_dir / "data" / "seeded" / "shanghai" / "room_types.json"

    with RoomTypeImporter(config) as importer:
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
        description="房型数据导入工具 - 将房型数据导入到 MongoDB"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="房型 JSON 文件路径 (默认: data/seeded/shanghai/room_types.json)",
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
    parser.add_argument("--collection", default="room_types", help="集合名称")
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

    config = RoomTypeImporterConfig(
        mongo_uri=args.uri,
        database=args.database,
        collection=args.collection,
        batch_size=args.batch_size,
        create_indexes=not args.no_indexes,
    )

    print("=" * 60)
    print("房型数据导入工具")
    print("=" * 60)
    print(f"  数据库: {config.database}")
    print(f"  集合:   {config.collection}")
    print(f"  导入模式: {mode.value}")
    print("=" * 60)

    try:
        with RoomTypeImporter(config) as importer:
            if mode is ImportMode.CLEAR:
                stats = importer.import_data(mode=mode)
            elif args.file:
                stats = importer.import_from_file(args.file, mode=mode)
            else:
                # Default: Shanghai seeded file
                base_dir = Path(__file__).resolve().parent.parent.parent
                data_file = (
                    base_dir / "data" / "seeded" / "shanghai" / "room_types.json"
                )
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
