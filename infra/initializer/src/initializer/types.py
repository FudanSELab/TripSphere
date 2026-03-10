"""
Shared domain types for all data importers.

These types are database-agnostic and are used by every importer
(POI, hotel, attraction, and any future additions).
"""

from dataclasses import dataclass, field
from enum import StrEnum


class ImportMode(StrEnum):
    """
    Import mode controlling how records are written to the target store.

    - REPLACE:     Drop the existing collection/table and fully reload all data.
    - UPSERT:      Update existing records by primary key, or insert new ones.
    - INSERT_ONLY: Insert only records that do not already exist; skip the rest.
    - CLEAR:       Clear the target collection/table without writing any data.
    """

    REPLACE = "replace"
    UPSERT = "upsert"
    INSERT_ONLY = "insert_only"
    CLEAR = "clear"


@dataclass
class ImportStats:
    """
    Statistics collected during a single import run.

    Attributes:
        total:         Total number of records processed.
        inserted:      Number of newly inserted documents/rows.
        updated:       Number of updated documents/rows.
        skipped:       Number of already-existing records that were skipped.
        errors:        Number of validation or write failures.
        error_details: Human-readable descriptions of each error.
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
