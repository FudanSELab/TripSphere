"""
Inventory Data Importer Module

This module provides functionality to import daily inventory data into
PostgreSQL for trip-inventory-service.

Usage:
    from initializer.inventories import InventoryImporter

    importer = InventoryImporter(postgres_dsn="postgresql://postgres:password@localhost:5432/inventory_db")
    importer.import_from_file("path/to/inventories.json", mode=ImportMode.REPLACE)
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from psycopg import Connection, Error, connect, sql

from initializer.config.settings import get_settings
from initializer.types import ImportMode, ImportStats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Importer config
# ---------------------------------------------------------------------------


@dataclass
class InventoryImporterConfig:
    """
    Configuration for the inventory importer.

    Attributes:
        postgres_dsn:  PostgreSQL connection DSN.
        table:         Table name for daily inventory rows.
        batch_size:    Number of rows to process per batch.
        ensure_schema: Whether to create the table/indexes if missing.
    """

    postgres_dsn: str = field(default_factory=lambda: get_settings().postgres.dsn)
    table: str = "daily_inventory"
    batch_size: int = field(default_factory=lambda: get_settings().importer.batch_size)
    ensure_schema: bool = True


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class InventoryImporter:
    """
    Daily inventory importer for PostgreSQL.

    Reads inventory documents from JSON files or Python objects and writes them
    into the configured PostgreSQL table using a schema compatible with
    Spring Data JPA's ``DailyInventoryEntity``.
    """

    def __init__(
        self, config: InventoryImporterConfig | None = None, **kwargs: Any
    ) -> None:
        """Initialise the inventory importer."""
        if config is None:
            config = InventoryImporterConfig()

        self._postgres_dsn = kwargs.get("postgres_dsn", config.postgres_dsn)
        self._table_name = kwargs.get("table", config.table)
        self._batch_size = kwargs.get("batch_size", config.batch_size)
        self._should_ensure_schema = kwargs.get("ensure_schema", config.ensure_schema)

        self._conn: Connection[Any] | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        """Establish PostgreSQL connection lazily."""
        if self._conn is None:
            logger.info("正在连接 PostgreSQL: %s", self._postgres_dsn)
            self._conn = connect(self._postgres_dsn)
            logger.info("已连接到数据表: %s", self._table_name)

    def _disconnect(self) -> None:
        """Close PostgreSQL connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("已断开 PostgreSQL 连接")

    @property
    def connection(self) -> Connection[Any]:
        """Return the PostgreSQL connection, connecting lazily if required."""
        if self._conn is None:
            self._connect()
        assert self._conn is not None
        return self._conn

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def _table_identifier(self) -> sql.Identifier:
        """Return the SQL identifier for the configured table name."""
        return sql.Identifier(self._table_name)

    def _ensure_schema(self) -> None:
        """Create the daily inventory table and required indexes if missing."""
        logger.info("正在确保 PostgreSQL 表结构存在…")
        table_ident = self._table_identifier()
        create_table_sql = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {} (
                id VARCHAR(36) PRIMARY KEY,
                sku_id VARCHAR(64) NOT NULL,
                inv_date DATE NOT NULL,
                total_qty INTEGER NOT NULL DEFAULT 0,
                available_qty INTEGER NOT NULL DEFAULT 0,
                locked_qty INTEGER NOT NULL DEFAULT 0,
                sold_qty INTEGER NOT NULL DEFAULT 0,
                price_currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
                price_units BIGINT NOT NULL DEFAULT 0,
                price_nanos INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT uk_sku_date UNIQUE (sku_id, inv_date)
            )
            """
        ).format(table_ident)
        create_index_sql = sql.SQL(
            """
            CREATE INDEX IF NOT EXISTS idx_daily_inventory_sku_date
            ON {} (sku_id, inv_date)
            """
        ).format(table_ident)

        with self.connection.cursor() as cursor:
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
        self.connection.commit()
        logger.info("PostgreSQL 表结构就绪")

    # ------------------------------------------------------------------
    # Validation / transformation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(value: Any) -> date:
        """Parse a JSON value into a ``date`` object."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError(f"无效日期值: {value!r}")

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """Parse a JSON value into a timezone-aware UTC ``datetime``."""
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        raise ValueError(f"无效时间戳值: {value!r}")

    @staticmethod
    def _validate_inventory(doc: dict[str, Any]) -> list[str]:
        """Validate a single inventory document."""
        errors: list[str] = []
        required_fields = [
            "id",
            "skuId",
            "invDate",
            "totalQty",
            "availableQty",
            "lockedQty",
            "soldQty",
            "priceCurrency",
            "priceUnits",
            "priceNanos",
            "updatedAt",
        ]
        for field_name in required_fields:
            if field_name not in doc or doc[field_name] in (None, ""):
                errors.append(f"缺少必需字段: {field_name}")

        if errors:
            return errors

        try:
            date.fromisoformat(str(doc["invDate"]))
        except ValueError:
            errors.append("invDate 必须是 YYYY-MM-DD 格式")

        try:
            datetime.fromisoformat(str(doc["updatedAt"]).replace("Z", "+00:00"))
        except ValueError:
            errors.append("updatedAt 必须是 ISO-8601 时间戳")

        quantity_fields = ("totalQty", "availableQty", "lockedQty", "soldQty")
        for field_name in quantity_fields:
            value = doc.get(field_name)
            if not isinstance(value, int):
                errors.append(f"{field_name} 必须是整数")
            elif value < 0:
                errors.append(f"{field_name} 不能为负数")

        total_qty = doc.get("totalQty")
        available_qty = doc.get("availableQty")
        locked_qty = doc.get("lockedQty")
        sold_qty = doc.get("soldQty")
        if all(
            isinstance(v, int) for v in (total_qty, available_qty, locked_qty, sold_qty)
        ):
            expected_available = total_qty - locked_qty - sold_qty
            if available_qty != expected_available:
                errors.append("availableQty 必须等于 totalQty - lockedQty - soldQty")

        price_currency = doc.get("priceCurrency")
        if not isinstance(price_currency, str) or len(price_currency) != 3:
            errors.append("priceCurrency 必须是 3 位货币代码")

        price_units = doc.get("priceUnits")
        if not isinstance(price_units, int):
            errors.append("priceUnits 必须是整数")

        price_nanos = doc.get("priceNanos")
        if not isinstance(price_nanos, int):
            errors.append("priceNanos 必须是整数")
        elif not 0 <= price_nanos < 1_000_000_000:
            errors.append("priceNanos 必须在 [0, 1000000000) 范围内")

        return errors

    @classmethod
    def _transform_inventory(cls, doc: dict[str, Any]) -> tuple[Any, ...]:
        """Convert a JSON document into a PostgreSQL row tuple."""
        return (
            str(doc["id"]),
            str(doc["skuId"]),
            cls._parse_date(doc["invDate"]),
            int(doc["totalQty"]),
            int(doc["availableQty"]),
            int(doc["lockedQty"]),
            int(doc["soldQty"]),
            str(doc["priceCurrency"]),
            int(doc["priceUnits"]),
            int(doc["priceNanos"]),
            cls._parse_timestamp(doc["updatedAt"]),
        )

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def _batch_iterator(
        self, inventories: Sequence[dict[str, Any]]
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield successive batches from *inventories*."""
        for i in range(0, len(inventories), self._batch_size):
            yield list(inventories[i : i + self._batch_size])

    def _insert_sql(self) -> sql.Composed:
        """Return the base INSERT statement."""
        return sql.SQL(
            """
            INSERT INTO {} (
                id,
                sku_id,
                inv_date,
                total_qty,
                available_qty,
                locked_qty,
                sold_qty,
                price_currency,
                price_units,
                price_nanos,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
        ).format(self._table_identifier())

    def _upsert_sql(self) -> sql.Composed:
        """Return the UPSERT statement keyed by ``(sku_id, inv_date)``."""
        return sql.SQL(
            """
            INSERT INTO {} (
                id,
                sku_id,
                inv_date,
                total_qty,
                available_qty,
                locked_qty,
                sold_qty,
                price_currency,
                price_units,
                price_nanos,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (sku_id, inv_date) DO UPDATE SET
                total_qty = EXCLUDED.total_qty,
                available_qty = EXCLUDED.available_qty,
                locked_qty = EXCLUDED.locked_qty,
                sold_qty = EXCLUDED.sold_qty,
                price_currency = EXCLUDED.price_currency,
                price_units = EXCLUDED.price_units,
                price_nanos = EXCLUDED.price_nanos,
                updated_at = EXCLUDED.updated_at
            """
        ).format(self._table_identifier())

    def _find_existing_keys(
        self, rows: Sequence[tuple[Any, ...]]
    ) -> set[tuple[str, date]]:
        """Fetch existing ``(sku_id, inv_date)`` keys for a batch."""
        if not rows:
            return set()

        tuple_placeholders = ", ".join(["(%s, %s)"] * len(rows))
        params: list[Any] = []
        for row in rows:
            params.extend([row[1], row[2]])

        query = sql.SQL(
            f"""
            SELECT sku_id, inv_date
            FROM {{table}}
            WHERE (sku_id, inv_date) IN ({tuple_placeholders})
            """
        ).format(table=self._table_identifier())

        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()

        return {(str(sku_id), inv_date) for sku_id, inv_date in records}

    # ------------------------------------------------------------------
    # Import modes
    # ------------------------------------------------------------------

    def _truncate_table(self) -> None:
        """Truncate the target table."""
        query = sql.SQL("TRUNCATE TABLE {}").format(self._table_identifier())
        with self.connection.cursor() as cursor:
            cursor.execute(query)
        self.connection.commit()

    def _import_clear(self) -> ImportStats:
        """Clear the target table without inserting any rows."""
        logger.info("CLEAR 模式: 正在清空数据表…")
        self._truncate_table()
        logger.info("数据表已清空")
        return ImportStats()

    def _import_replace(self, inventories: Sequence[dict[str, Any]]) -> ImportStats:
        """Truncate and fully reload the target table."""
        stats = ImportStats(total=len(inventories))
        logger.info("REPLACE 模式: 正在清空现有数据…")
        self._truncate_table()

        insert_sql = self._insert_sql()
        logger.info("正在插入 %s 条库存记录…", len(inventories))

        for batch in self._batch_iterator(inventories):
            rows: list[tuple[Any, ...]] = []
            for doc in batch:
                errors = self._validate_inventory(doc)
                if errors:
                    stats.errors += 1
                    sku_id = doc.get("skuId", "unknown")
                    inv_date = doc.get("invDate", "unknown")
                    stats.error_details.append(
                        f"Inventory '{sku_id}/{inv_date}': {', '.join(errors)}"
                    )
                    continue
                rows.append(self._transform_inventory(doc))

            if not rows:
                continue

            try:
                with self.connection.cursor() as cursor:
                    cursor.executemany(insert_sql, rows)
                self.connection.commit()
                stats.inserted += len(rows)
            except Error as exc:
                self.connection.rollback()
                stats.errors += len(rows)
                stats.error_details.append(f"批量写入错误: {exc}")

        return stats

    def _import_upsert(self, inventories: Sequence[dict[str, Any]]) -> ImportStats:
        """Upsert rows by the unique key ``(sku_id, inv_date)``."""
        stats = ImportStats(total=len(inventories))
        upsert_sql = self._upsert_sql()
        logger.info("UPSERT 模式: 正在处理 %s 条库存记录…", len(inventories))

        for batch in self._batch_iterator(inventories):
            rows: list[tuple[Any, ...]] = []
            for doc in batch:
                errors = self._validate_inventory(doc)
                if errors:
                    stats.errors += 1
                    sku_id = doc.get("skuId", "unknown")
                    inv_date = doc.get("invDate", "unknown")
                    stats.error_details.append(
                        f"Inventory '{sku_id}/{inv_date}': {', '.join(errors)}"
                    )
                    continue
                rows.append(self._transform_inventory(doc))

            if not rows:
                continue

            try:
                existing_keys = self._find_existing_keys(rows)
                with self.connection.cursor() as cursor:
                    cursor.executemany(upsert_sql, rows)
                self.connection.commit()

                updated = sum(
                    1 for row in rows if (str(row[1]), row[2]) in existing_keys
                )
                inserted = len(rows) - updated
                stats.updated += updated
                stats.inserted += inserted
            except Error as exc:
                self.connection.rollback()
                stats.errors += len(rows)
                stats.error_details.append(f"批量写入错误: {exc}")

        return stats

    def _import_insert_only(self, inventories: Sequence[dict[str, Any]]) -> ImportStats:
        """Insert only rows that do not already exist."""
        stats = ImportStats(total=len(inventories))
        insert_sql = sql.SQL(
            """
            INSERT INTO {} (
                id,
                sku_id,
                inv_date,
                total_qty,
                available_qty,
                locked_qty,
                sold_qty,
                price_currency,
                price_units,
                price_nanos,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (sku_id, inv_date) DO NOTHING
            """
        ).format(self._table_identifier())
        logger.info("INSERT_ONLY 模式: 正在处理 %s 条库存记录…", len(inventories))

        for batch in self._batch_iterator(inventories):
            rows: list[tuple[Any, ...]] = []
            for doc in batch:
                errors = self._validate_inventory(doc)
                if errors:
                    stats.errors += 1
                    sku_id = doc.get("skuId", "unknown")
                    inv_date = doc.get("invDate", "unknown")
                    stats.error_details.append(
                        f"Inventory '{sku_id}/{inv_date}': {', '.join(errors)}"
                    )
                    continue
                rows.append(self._transform_inventory(doc))

            if not rows:
                continue

            try:
                existing_keys = self._find_existing_keys(rows)
                with self.connection.cursor() as cursor:
                    cursor.executemany(insert_sql, rows)
                self.connection.commit()

                inserted = len(rows) - len(existing_keys)
                skipped = len(rows) - inserted
                stats.inserted += inserted
                stats.skipped += skipped
            except Error as exc:
                self.connection.rollback()
                stats.errors += len(rows)
                stats.error_details.append(f"批量写入错误: {exc}")

        return stats

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_data(
        self,
        inventories: Sequence[dict[str, Any]] = (),
        mode: ImportMode = ImportMode.UPSERT,
    ) -> ImportStats:
        """Import inventory data into PostgreSQL."""
        logger.info("开始操作 (模式: %s)", mode.value)

        try:
            if self._should_ensure_schema:
                self._ensure_schema()

            if mode is ImportMode.CLEAR:
                stats = self._import_clear()
            else:
                logger.info("待处理记录数: %s", len(inventories))
                mode_methods = {
                    ImportMode.REPLACE: self._import_replace,
                    ImportMode.UPSERT: self._import_upsert,
                    ImportMode.INSERT_ONLY: self._import_insert_only,
                }
                stats = mode_methods[mode](inventories)

            logger.info("操作完成: %s", stats)
            return stats
        except Error as exc:
            logger.error("PostgreSQL 操作失败: %s", exc)
            raise

    def import_from_file(
        self,
        file_path: str | Path,
        mode: ImportMode = ImportMode.UPSERT,
        encoding: str = "utf-8",
    ) -> ImportStats:
        """Import inventory data from a JSON file."""
        if mode is ImportMode.CLEAR:
            return self.import_data(mode=mode)

        file_path = Path(file_path)
        logger.info("正在读取文件: %s", file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding=encoding) as f:
            inventories = json.load(f)

        if not isinstance(inventories, list):
            raise ValueError("JSON 文件必须包含库存文档数组")

        logger.info("已加载 %s 条库存记录", len(inventories))
        return self.import_data(inventories, mode=mode)

    def get_stats(self) -> dict[str, Any]:
        """Return current table statistics."""
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(self._table_identifier())
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            count = int(cursor.fetchone()[0])
        return {
            "table": self._table_name,
            "row_count": count,
        }

    def close(self) -> None:
        """Close the PostgreSQL connection."""
        self._disconnect()

    def __enter__(self) -> "InventoryImporter":
        """Context manager entry."""
        self._connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def import_shanghai_inventories(
    mode: ImportMode = ImportMode.UPSERT,
    config: InventoryImporterConfig | None = None,
) -> ImportStats:
    """Convenience function to import the seeded Shanghai inventory data."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = base_dir / "data" / "seeded" / "shanghai" / "inventories.json"

    with InventoryImporter(config) as importer:
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
        description="库存数据导入工具 - 将 inventories.json 导入到 PostgreSQL"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="库存 JSON 文件路径 (默认: data/seeded/shanghai/inventories.json)",
    )
    parser.add_argument(
        "--mode",
        choices=["replace", "upsert", "insert_only", "clear"],
        default="upsert",
        help=(
            "操作模式: replace(替换), upsert(更新或插入), "
            "insert_only(仅插入新数据), clear(仅清空数据表)"
        ),
    )
    parser.add_argument(
        "--dsn",
        default=get_settings().postgres.dsn,
        help="PostgreSQL DSN",
    )
    parser.add_argument("--table", default="daily_inventory", help="数据表名称")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=get_settings().importer.batch_size,
        help="批量操作大小",
    )
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="跳过自动建表和索引",
    )

    args = parser.parse_args()

    mode_map = {
        "replace": ImportMode.REPLACE,
        "upsert": ImportMode.UPSERT,
        "insert_only": ImportMode.INSERT_ONLY,
        "clear": ImportMode.CLEAR,
    }
    mode = mode_map[args.mode]

    config = InventoryImporterConfig(
        postgres_dsn=args.dsn,
        table=args.table,
        batch_size=args.batch_size,
        ensure_schema=not args.no_schema,
    )

    print("=" * 60)
    print("库存数据导入工具")
    print("=" * 60)
    print(f"  数据表:   {config.table}")
    print(f"  导入模式: {mode.value}")
    print(f"  DSN:      {config.postgres_dsn}")
    print("=" * 60)

    try:
        with InventoryImporter(config) as importer:
            if mode is ImportMode.CLEAR:
                stats = importer.import_data(mode=mode)
            elif args.file:
                stats = importer.import_from_file(args.file, mode=mode)
            else:
                base_dir = Path(__file__).resolve().parent.parent.parent
                data_file = (
                    base_dir / "data" / "seeded" / "shanghai" / "inventories.json"
                )
                stats = importer.import_from_file(data_file, mode=mode)

            print("\n" + "=" * 60)
            print("导入完成!")
            print(f"  {stats}")

            if stats.errors > 0:
                print("\n错误详情 (前10条):")
                for error in stats.error_details[:10]:
                    print(f"  - {error}")

            table_stats = importer.get_stats()
            print("\n数据表统计:")
            print(f"  行数: {table_stats['row_count']}")
            print(f"  表名: {table_stats['table']}")
            print("=" * 60)
    except FileNotFoundError as exc:
        print(f"错误: {exc}")
        sys.exit(1)
    except Error as exc:
        print(f"数据库错误: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
