from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd
from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from review_summary.clients.reviews import (
    ReviewRecord,
    ReviewServiceClient,
    TargetType,
)
from review_summary.index.review_snapshot import (
    compute_review_snapshot,
    reviews_to_text_units,
)
from review_summary.models import Entity, TextUnit
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

ReviewStateStatus = Literal[
    "success",
    "empty_reviews",
    "index_missing",
    "dependency_failure",
]
PreflightStatus = Literal["ready", "empty_reviews", "index_missing"]
ReviewIndexValidationMode = Literal["strict", "pinned"]


class ReviewEvidence(BaseModel):
    review_id: str
    excerpt: str
    rating: int
    updated_at: str | None = None


class ReviewState(BaseModel):
    status: ReviewStateStatus
    target_id: str
    target_type: TargetType
    review_snapshot: str | None = None
    answer: str | None = None
    evidence: list[ReviewEvidence] | None = None
    message: str | None = None
    dependency: str | None = None
    error_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


@dataclass(frozen=True, slots=True)
class ReviewPreflightResult:
    status: PreflightStatus
    snapshot: str
    reviews: list[ReviewRecord]
    message: str | None = None


class ReviewDependencyError(RuntimeError):
    def __init__(self, dependency: str, error_code: str, message: str) -> None:
        super().__init__(message)
        self.dependency = dependency
        self.error_code = error_code


class ReviewIndexPreflight:
    def __init__(
        self,
        review_client: ReviewServiceClient,
        text_unit_store: TextUnitVectorStore,
        entity_store: EntityVectorStore,
        neo4j_driver: AsyncDriver,
        validation_mode: ReviewIndexValidationMode = "strict",
    ) -> None:
        self._review_client = review_client
        self._text_unit_store = text_unit_store
        self._entity_store = entity_store
        self._neo4j_driver = neo4j_driver
        self._validation_mode = validation_mode

    async def run(
        self,
        target_id: str,
        target_type: TargetType,
    ) -> ReviewPreflightResult:
        reviews: list[ReviewRecord] = []
        snapshot: str | None = None
        if self._validation_mode == "strict":
            try:
                reviews = await self._review_client.list_all(target_id, target_type)
            except Exception as exc:
                raise ReviewDependencyError(
                    "review_service",
                    "REVIEW_SERVICE_UNAVAILABLE",
                    "Unable to read current reviews",
                ) from exc

            snapshot = compute_review_snapshot(reviews)
            if not reviews:
                return ReviewPreflightResult(
                    status="empty_reviews",
                    snapshot=snapshot,
                    reviews=reviews,
                    message="该目标目前还没有评论。",
                )

        try:
            text_units = await self._text_unit_store.find_by_target(
                target_id,
                target_type.value,
            )
            entities = await self._entity_store.find_by_target(
                target_id,
                target_type.value,
            )
        except Exception as exc:
            raise ReviewDependencyError(
                "qdrant",
                "QDRANT_UNAVAILABLE",
                "Unable to inspect the review vector index",
            ) from exc

        if self._validation_mode == "pinned":
            snapshot = _pinned_text_unit_snapshot(
                text_units,
                target_id,
                target_type,
            )
            if snapshot is None:
                return _missing_index("", reviews, "固定评论文本索引缺失或不一致。")
        elif snapshot is None or not _text_units_match_live_reviews(
            text_units,
            reviews,
            target_id,
            target_type,
            snapshot,
        ):
            return _missing_index(snapshot or "", reviews, "评论文本索引缺失或已过期。")

        if not _entities_match_snapshot(
            entities,
            target_id,
            target_type,
            snapshot,
        ):
            return _missing_index(snapshot, reviews, "评论实体索引缺失或已过期。")

        try:
            (
                graph_entity_ids,
                graph_relationship_ids,
                graph_snapshot_valid,
            ) = await _load_graph_state(
                self._neo4j_driver,
                target_id,
                target_type,
                snapshot,
            )
        except Exception as exc:
            raise ReviewDependencyError(
                "neo4j",
                "NEO4J_UNAVAILABLE",
                "Unable to inspect the review graph index",
            ) from exc

        vector_entity_ids = {entity.id for entity in entities}
        expected_entity_ids = _collect_reference_ids(text_units, "entity_ids")
        expected_relationship_ids = _collect_reference_ids(
            text_units,
            "relationship_ids",
        )
        if (
            not graph_snapshot_valid
            or expected_entity_ids is None
            or expected_relationship_ids is None
            or expected_entity_ids != vector_entity_ids
            or graph_entity_ids != vector_entity_ids
            or graph_relationship_ids != expected_relationship_ids
        ):
            return _missing_index(snapshot, reviews, "评论图索引缺失、部分完成或已过期。")

        return ReviewPreflightResult(
            status="ready",
            snapshot=snapshot,
            reviews=reviews,
        )


def evidence_from_context(
    context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame],
) -> list[ReviewEvidence]:
    if not isinstance(context_data, dict):
        return []

    sources = context_data.get("sources")
    if not isinstance(sources, pd.DataFrame) or sources.empty:
        return []

    evidence: list[ReviewEvidence] = []
    for source in sources.to_dict("records"):
        review_id = str(source.get("review_id") or source.get("id") or "").strip()
        excerpt = str(source.get("text") or "").strip()
        try:
            rating = int(source.get("rating"))
        except (TypeError, ValueError):
            continue
        if not review_id or not excerpt or not 1 <= rating <= 5:
            continue

        raw_updated_at = source.get("updated_at")
        updated_at = (
            str(raw_updated_at).strip() if raw_updated_at is not None else None
        )
        evidence.append(
            ReviewEvidence(
                review_id=review_id,
                excerpt=excerpt[:500],
                rating=rating,
                updated_at=updated_at or None,
            )
        )
    return evidence


def _missing_index(
    snapshot: str,
    reviews: list[ReviewRecord],
    message: str,
) -> ReviewPreflightResult:
    return ReviewPreflightResult(
        status="index_missing",
        snapshot=snapshot,
        reviews=reviews,
        message=message,
    )


def _text_units_match_live_reviews(
    text_units: list[TextUnit],
    reviews: list[ReviewRecord],
    target_id: str,
    target_type: TargetType,
    snapshot: str,
) -> bool:
    if len(text_units) != len(reviews):
        return False

    live_reviews = {review.id: review for review in reviews}
    if len(live_reviews) != len(reviews):
        return False
    expected_text_units: dict[str, TextUnit] = {}
    for expected_text_unit in reviews_to_text_units(
        reviews,
        target_id,
        target_type,
        snapshot,
    ):
        expected_review_id = (expected_text_unit.attributes or {}).get("review_id")
        if not isinstance(expected_review_id, str):
            return False
        expected_text_units[expected_review_id] = expected_text_unit

    indexed_review_ids: set[str] = set()
    for text_unit in text_units:
        attributes = text_unit.attributes or {}
        review_id = attributes.get("review_id")
        if not isinstance(review_id, str):
            return False
        review = live_reviews.get(review_id)
        if review is None or review_id in indexed_review_ids:
            return False
        expected_text_unit = expected_text_units.get(review_id)
        if expected_text_unit is None:
            return False
        if (
            text_unit.id != expected_text_unit.id
            or text_unit.text != expected_text_unit.text
            or attributes.get("target_id") != target_id
            or attributes.get("target_type") != target_type.value
            or attributes.get("review_snapshot") != snapshot
            or attributes.get("user_id") != review.user_id
            or attributes.get("rating") != review.rating
            or attributes.get("updated_at") != review.updated_at
        ):
            return False
        indexed_review_ids.add(review_id)

    return indexed_review_ids == set(live_reviews)


def _pinned_text_unit_snapshot(
    text_units: list[TextUnit],
    target_id: str,
    target_type: TargetType,
) -> str | None:
    if not text_units:
        return None

    snapshots: set[str] = set()
    review_ids: set[str] = set()
    for text_unit in text_units:
        attributes = text_unit.attributes or {}
        snapshot = attributes.get("review_snapshot")
        review_id = attributes.get("review_id")
        rating = attributes.get("rating")
        updated_at = attributes.get("updated_at")
        if (
            not text_unit.text.strip()
            or not isinstance(snapshot, str)
            or not snapshot.strip()
            or not isinstance(review_id, str)
            or not review_id.strip()
            or review_id in review_ids
            or not isinstance(rating, int)
            or isinstance(rating, bool)
            or not 1 <= rating <= 5
            or not isinstance(updated_at, str)
            or not updated_at.strip()
            or attributes.get("target_id") != target_id
            or attributes.get("target_type") != target_type.value
        ):
            return None
        snapshots.add(snapshot)
        review_ids.add(review_id)

    if len(snapshots) != 1:
        return None
    return snapshots.pop()


def _entities_match_snapshot(
    entities: list[Entity],
    target_id: str,
    target_type: TargetType,
    snapshot: str,
) -> bool:
    if not entities:
        return False
    return all(
        (entity.attributes or {}).get("target_id") == target_id
        and (entity.attributes or {}).get("target_type") == target_type.value
        and (entity.attributes or {}).get("review_snapshot") == snapshot
        for entity in entities
    )


def _collect_reference_ids(
    text_units: list[TextUnit],
    field_name: Literal["entity_ids", "relationship_ids"],
) -> set[str] | None:
    reference_ids: set[str] = set()
    for text_unit in text_units:
        values = getattr(text_unit, field_name)
        if values is None:
            return None
        if any(not value.strip() for value in values):
            return None
        reference_ids.update(values)
    return reference_ids


async def _load_graph_state(
    driver: AsyncDriver,
    target_id: str,
    target_type: TargetType,
    snapshot: str,
) -> tuple[set[str], set[str], bool]:
    query = """
    MATCH (entity:Entity)
    WHERE entity.target_id = $target_id
      AND entity.target_type = $target_type
    WITH collect({id: entity.id, snapshot: entity.review_snapshot}) AS entities
    OPTIONAL MATCH ()-[relationship:RELATES]->()
    WHERE relationship.target_id = $target_id
      AND relationship.target_type = $target_type
    RETURN entities,
           collect(
             CASE WHEN relationship IS NULL THEN null
             ELSE {id: relationship.id, snapshot: relationship.review_snapshot}
             END
           ) AS relationships
    """
    async with driver.session() as session:  # pyright: ignore
        result = await session.run(
            query,
            target_id=target_id,
            target_type=target_type.value,
        )
        record = await result.single()

    if record is None:
        return set(), set(), False

    entities = record["entities"] or []
    relationships = record["relationships"] or []
    entity_ids = {
        str(entity["id"])
        for entity in entities
        if entity.get("id") is not None
    }
    relationship_ids = {
        str(relationship["id"])
        for relationship in relationships
        if relationship.get("id") is not None
    }
    return (
        entity_ids,
        relationship_ids,
        bool(entity_ids)
        and len(entity_ids) == len(entities)
        and all(entity.get("snapshot") == snapshot for entity in entities)
        and len(relationship_ids) == len(relationships)
        and all(
            relationship.get("id") is not None
            and relationship.get("snapshot") == snapshot
            for relationship in relationships
        ),
    )
