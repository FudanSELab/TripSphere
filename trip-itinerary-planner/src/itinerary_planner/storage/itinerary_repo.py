"""MongoDB repository for persisting AI-planned itineraries."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

COLLECTION = "itinerary_plans"


class ItineraryRepo:
    """Async CRUD operations for the ``itinerary_plans`` MongoDB collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._col: AsyncIOMotorCollection = db[COLLECTION]  # type: ignore[type-arg]

    # ── Write operations ───────────────────────────────────────────────────

    async def ensure_indexes(self) -> None:
        """Create indexes on startup (idempotent)."""
        await self._col.create_index(
            [("user_id", 1), ("updated_at", -1)], background=True
        )
        logger.info("ItineraryRepo indexes ensured")

    async def save(
        self,
        *,
        itinerary_id: str,
        user_id: str,
        destination: str,
        start_date: str,
        end_date: str,
        itinerary: dict[str, Any],
        markdown_content: str,
    ) -> None:
        """Insert a new itinerary document (upsert by _id for idempotency)."""
        now = datetime.now(timezone.utc)
        doc = {
            "_id": itinerary_id,
            "user_id": user_id,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "itinerary": itinerary,
            "markdown_content": markdown_content,
            "created_at": now,
            "updated_at": now,
        }
        await self._col.replace_one({"_id": itinerary_id}, doc, upsert=True)
        logger.info(
            "Saved itinerary %s for user %s (%s)", itinerary_id, user_id, destination
        )

    async def update(
        self,
        *,
        itinerary_id: str,
        user_id: str,
        itinerary: dict[str, Any],
        markdown_content: str | None = None,
    ) -> bool:
        """Update the itinerary data for a user-owned document.

        Returns True if the document was found and updated.
        """
        update: dict[str, Any] = {
            "$set": {
                "itinerary": itinerary,
                "updated_at": datetime.now(timezone.utc),
            }
        }
        if markdown_content is not None:
            update["$set"]["markdown_content"] = markdown_content

        result = await self._col.update_one(
            {"_id": itinerary_id, "user_id": user_id}, update
        )
        found = result.matched_count > 0
        if found:
            logger.info("Updated itinerary %s for user %s", itinerary_id, user_id)
        else:
            logger.warning(
                "Update failed — itinerary %s not found for user %s",
                itinerary_id,
                user_id,
            )
        return found

    async def delete(self, *, itinerary_id: str, user_id: str) -> bool:
        """Delete a user-owned document. Returns True if deleted."""
        result = await self._col.delete_one(
            {"_id": itinerary_id, "user_id": user_id}
        )
        deleted = result.deleted_count > 0
        if deleted:
            logger.info("Deleted itinerary %s for user %s", itinerary_id, user_id)
        return deleted

    # ── Read operations ────────────────────────────────────────────────────

    async def get(self, *, itinerary_id: str, user_id: str) -> dict[str, Any] | None:
        """Fetch a single itinerary owned by user_id."""
        doc = await self._col.find_one(
            {"_id": itinerary_id, "user_id": user_id}
        )
        return doc  # type: ignore[return-value]

    async def get_any(self, *, itinerary_id: str) -> dict[str, Any] | None:
        """Fetch a single itinerary without ownership check (for internal use)."""
        doc = await self._col.find_one({"_id": itinerary_id})
        return doc  # type: ignore[return-value]

    async def list_by_user(
        self, *, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List itineraries for a user, newest first, without full itinerary JSON."""
        projection: dict[str, Any] = {
            "_id": 1,
            "destination": 1,
            "start_date": 1,
            "end_date": 1,
            "created_at": 1,
            "updated_at": 1,
            # Include day count from nested itinerary
            "day_count": {"$size": {"$ifNull": ["$itinerary.day_plans", []]}},
        }
        cursor = (  # type: ignore[misc]
            self._col.find({"user_id": user_id}, projection)  # type: ignore[arg-type]
            .sort("updated_at", -1)
            .limit(limit)
        )
        results: list[dict[str, Any]] = []
        async for doc in cursor:  # type: ignore[union-attr]
            results.append(doc)  # type: ignore[arg-type]
        return results
