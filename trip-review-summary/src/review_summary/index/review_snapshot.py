from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

from review_summary.clients.reviews import ReviewRecord, TargetType
from review_summary.models import TextUnit


def compute_review_snapshot(reviews: Sequence[ReviewRecord]) -> str:
    review_versions = sorted((review.id, review.updated_at) for review in reviews)
    canonical_versions = json.dumps(
        review_versions,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical_versions).hexdigest()


def reviews_to_text_units(
    reviews: Sequence[ReviewRecord],
    target_id: str,
    target_type: TargetType,
    snapshot: str,
) -> list[TextUnit]:
    text_units: list[TextUnit] = []
    for review in reviews:
        if review.target_id != target_id or review.target_type != target_type:
            raise ValueError(f"Review {review.id!r} does not belong to the target")

        content = review.content.strip()
        source_text = f"Overall rating: {review.rating}/5."
        if content:
            source_text = f"{source_text}\nReview: {content}"
        else:
            source_text = f"{source_text} No written review was provided."

        text_unit_id = str(
            uuid5(
                NAMESPACE_URL,
                f"tripsphere:review:{target_type.value}:{target_id}:{review.id}",
            )
        )
        text_units.append(
            TextUnit(
                id=text_unit_id,
                readable_id=review.id,
                text=source_text,
                entity_ids=[],
                relationship_ids=[],
                document_id=review.id,
                attributes={
                    "target_id": target_id,
                    "target_type": target_type.value,
                    "review_snapshot": snapshot,
                    "review_id": review.id,
                    "user_id": review.user_id,
                    "rating": review.rating,
                    "updated_at": review.updated_at,
                },
            )
        )
    return text_units
