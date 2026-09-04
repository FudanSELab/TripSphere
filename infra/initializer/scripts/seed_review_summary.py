#!/usr/bin/env -S uv run --script
"""Generate deterministic hotel reviews and build pinned review-summary indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import requests
from pymongo import MongoClient, UpdateOne

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_VERSION = "review-summary-dataset-v2-direct"
HOTEL_ENTITY_TYPE = 1
TARGET_TYPE = "hotel"
VECTOR_SIZE = 3072
TEXT_COLLECTION = "review_summary_text_units"
ENTITY_COLLECTION = "review_summary_entities"
RATINGS = (5, 4, 4, 3, 5, 4, 3, 2, 5, 4)

POSITIVE_EXPERIENCES = (
    "客房卫生和床品舒适度整体令人满意",
    "前台沟通顺畅，入住和退房办理比较利落",
    "公共区域维护得比较整洁，入住感受稳定",
    "工作人员回应需求比较及时，服务态度自然",
    "房间休息体验不错，适合作为旅途中的落脚点",
)
BALANCED_EXPERIENCES = (
    "整体体验符合预期，不过高峰时段公共区域会稍显忙碌",
    "服务和卫生表现较稳，部分细节仍有提升空间",
    "基本需求都能满足，房间配置偏实用而不是豪华",
    "入住过程比较顺利，但繁忙时段等待时间略长",
    "整体住得舒服，价格与体验是否匹配取决于预订时段",
)
CRITICAL_EXPERIENCES = (
    "基础卫生尚可，但隔音和设施维护还有改进空间",
    "工作人员能够处理问题，不过响应速度不够稳定",
    "房间能够满足基本住宿需求，但部分细节显得陈旧",
    "整体体验中规中矩，高峰时段的服务衔接可以更好",
    "位置是主要优势，客房舒适度和细节管理仍需提升",
)
MINOR_DRAWBACKS = (
    "如果对隔音特别敏感，入住时可以提前沟通房间位置。",
    "热门时段客流较多，建议预留办理入住的时间。",
    "部分房型空间和朝向不同，预订前最好确认具体信息。",
    "周边出行较方便，但高峰时段叫车可能需要等待。",
    "对设施新旧程度要求很高的住客可以先确认具体房型。",
)
TAG_EXPERIENCES = {
    "免费停车": "酒店资料标注提供免费停车，对自驾出行比较友好",
    "泳池": "酒店资料显示配有泳池，休闲需求有更多选择",
    "桑拿": "酒店资料显示提供桑拿设施，行程后可以安排放松",
    "管家服务": "酒店资料标注提供管家服务，适合重视服务响应的住客",
}


@dataclass(frozen=True, slots=True)
class Config:
    mongo_uri: str
    embedding_base_url: str
    embedding_api_key: str
    embedding_model: str
    qdrant_url: str
    neo4j_url: str
    neo4j_username: str
    neo4j_password: str
    manifest_path: Path
    min_reviews: int
    max_reviews: int
    concurrency: int
    retries: int


class Manifest:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.verified = self._load_verified()

    def is_verified(self, hotel_id: str) -> bool:
        return hotel_id in self.verified

    def append(self, record: dict[str, Any]) -> None:
        payload = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "seed_version": SEED_VERSION,
            **record,
        }
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(payload, ensure_ascii=False) + "\n")
            if payload.get("status") == "index_verified":
                self.verified.add(str(payload["hotel_id"]))

    def _load_verified(self) -> set[str]:
        if not self.path.exists():
            return set()
        latest: dict[str, str] = {}
        with self.path.open(encoding="utf-8") as source:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("seed_version") != SEED_VERSION:
                    continue
                hotel_id = record.get("hotel_id")
                status = record.get("status")
                if isinstance(hotel_id, str) and isinstance(status, str):
                    latest[hotel_id] = status
        return {
            hotel_id
            for hotel_id, status in latest.items()
            if status == "index_verified"
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic hotel reviews and directly build the minimal "
            "pinned review-summary indexes."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write reviews and indexes; without this flag only a preview is shown.",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-reviews", type=int, default=5)
    parser.add_argument("--max-reviews", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=BASE_DIR / "data" / "temp" / "review_seed_manifest.jsonl",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Rebuild hotels already marked index_verified in the manifest.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    if args.min_reviews < 1 or args.max_reviews < args.min_reviews:
        raise ValueError("review range must be positive and ordered")
    if not 1 <= args.concurrency <= 4:
        raise ValueError("concurrency must be between 1 and 4")
    if args.retries < 0:
        raise ValueError("retries must not be negative")
    if args.offset < 0 or (args.limit is not None and args.limit < 1):
        raise ValueError("offset must be non-negative and limit must be positive")

    return Config(
        mongo_uri=os.getenv(
            "MONGODB_URI",
            "mongodb://root:fudanse@localhost:27017/?authSource=admin",
        ),
        embedding_base_url=os.getenv(
            "OPENAI_BASE_URL", "http://localhost:28080/v1"
        ).rstrip("/"),
        embedding_api_key=os.getenv("OPENAI_API_KEY", "api-key"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/"),
        neo4j_url=os.getenv("NEO4J_HTTP_URL", "http://localhost:7474").rstrip("/"),
        neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "fudanse@fudan.edu.cn"),
        manifest_path=args.manifest,
        min_reviews=args.min_reviews,
        max_reviews=args.max_reviews,
        concurrency=args.concurrency,
        retries=args.retries,
    )


def load_hotels(config: Config, offset: int, limit: int | None) -> list[dict[str, Any]]:
    with MongoClient(config.mongo_uri, tz_aware=True) as client:
        cursor = (
            client.hotel_db.hotels.find(
                {},
                {
                    "_id": 1,
                    "name": 1,
                    "address": 1,
                    "tags": 1,
                    "amenities": 1,
                },
            )
            .sort("_id", 1)
            .skip(offset)
        )
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)


def stable_review_count(hotel_id: str, minimum: int, maximum: int) -> int:
    digest = hashlib.sha256(hotel_id.encode()).digest()
    return minimum + int.from_bytes(digest[:4], "big") % (maximum - minimum + 1)


def build_review_content(hotel: dict[str, Any], rating: int, index: int) -> str:
    hotel_id = str(hotel["_id"])
    rng = random.Random(f"{SEED_VERSION}:{hotel_id}:{index}")
    name = str(hotel.get("name") or "这家酒店").strip()
    address = hotel.get("address") or {}
    district = str(address.get("district") or "").strip()
    detailed = str(address.get("detailed") or "").strip()
    tags = [
        str(tag).strip()
        for tag in [*(hotel.get("tags") or []), *(hotel.get("amenities") or [])]
        if str(tag).strip()
    ]

    location = f"位于{district}" if district else "所在位置容易找到"
    if detailed and index % 3 == 0:
        location = f"地址在{detailed}"
    opening = rng.choice(
        (
            f"这次入住{name}，{location}，按酒店地址前往比较顺利。",
            f"选择{name}主要考虑{location}，实际到店过程比较顺畅。",
            f"在{name}住了一晚，{location}，整体出行安排比较方便。",
        )
    )
    if rating >= 5:
        experience = rng.choice(POSITIVE_EXPERIENCES)
    elif rating >= 3:
        experience = rng.choice(BALANCED_EXPERIENCES)
    else:
        experience = rng.choice(CRITICAL_EXPERIENCES)

    parts = [opening, f"{experience}。"]
    if tags:
        tag = tags[index % len(tags)]
        tag_experience = TAG_EXPERIENCES.get(
            tag,
            f"酒店资料中标注了{tag}，可按需要提前确认使用安排",
        )
        parts.append(f"{tag_experience}。")
    parts.append(MINOR_DRAWBACKS[index % len(MINOR_DRAWBACKS)])
    return "".join(parts)


def build_seed_reviews(
    hotel: dict[str, Any], minimum: int, maximum: int
) -> list[dict[str, Any]]:
    hotel_id = str(hotel["_id"])
    count = stable_review_count(hotel_id, minimum, maximum)
    digest = hashlib.sha256(hotel_id.encode()).digest()
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=UTC) + timedelta(
        days=int.from_bytes(digest[4:8], "big") % 180
    )
    reviews: list[dict[str, Any]] = []
    for index in range(count):
        review_id = str(
            uuid5(
                NAMESPACE_URL,
                f"tripsphere:{SEED_VERSION}:{hotel_id}:{index + 1}",
            )
        )
        timestamp = base_time + timedelta(days=index, minutes=index * 7)
        rating = RATINGS[index % len(RATINGS)]
        reviews.append(
            {
                "_id": review_id,
                "user_id": f"review-summary-dataset-{hotel_id[-8:]}-{index + 1:02d}",
                "entity_type": HOTEL_ENTITY_TYPE,
                "entity_id": hotel_id,
                "rating": rating,
                "content": build_review_content(hotel, rating, index),
                "images": [],
                "dimensions": {},
                "created_at": timestamp,
                "updated_at": timestamp,
                "seed_source": SEED_VERSION,
            }
        )
    return reviews


def seed_and_load_reviews(
    config: Config, hotel: dict[str, Any]
) -> tuple[list[dict[str, Any]], frozenset[str]]:
    seed_reviews = build_seed_reviews(hotel, config.min_reviews, config.max_reviews)
    seed_ids = frozenset(str(review["_id"]) for review in seed_reviews)
    operations = []
    for review in seed_reviews:
        review_id = review["_id"]
        fields = {key: value for key, value in review.items() if key != "_id"}
        operations.append(
            UpdateOne(
                {"_id": review_id},
                {"$set": fields, "$setOnInsert": {"_id": review_id}},
                upsert=True,
            )
        )

    hotel_id = str(hotel["_id"])
    seed_scope = {
        "entity_type": HOTEL_ENTITY_TYPE,
        "entity_id": hotel_id,
        "seed_source": SEED_VERSION,
    }
    with MongoClient(config.mongo_uri, tz_aware=True) as client:
        collection = client.review_db.reviews
        collection.delete_many({**seed_scope, "_id": {"$nin": list(seed_ids)}})
        collection.bulk_write(operations, ordered=True)
        reviews = list(
            collection.find({**seed_scope, "_id": {"$in": list(seed_ids)}}).sort(
                "_id", 1
            )
        )
    if len(reviews) != len(seed_ids):
        raise RuntimeError("MongoDB seed review count differs from generated data")
    return reviews, seed_ids


def review_version(review: dict[str, Any]) -> str:
    updated_at = review.get("updated_at")
    if not isinstance(updated_at, datetime):
        raise ValueError(f"Review {review.get('_id')} has invalid updated_at")
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    timestamp = updated_at.astimezone(UTC)
    seconds = int(timestamp.timestamp())
    nanos = timestamp.microsecond * 1000
    return f"{seconds}:{nanos:09d}"


def compute_snapshot(reviews: list[dict[str, Any]]) -> str:
    versions = sorted(
        (str(review["_id"]), review_version(review)) for review in reviews
    )
    canonical = json.dumps(
        versions,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def source_text(review: dict[str, Any]) -> str:
    rating = int(review["rating"])
    content = str(review.get("content") or "").strip()
    if content:
        return f"Overall rating: {rating}/5.\nReview: {content}"
    return f"Overall rating: {rating}/5. No written review was provided."


def embed_texts(config: Config, texts: list[str]) -> list[list[float]]:
    last_error: Exception | None = None
    for attempt in range(config.retries + 2):
        try:
            response = requests.post(
                f"{config.embedding_base_url}/embeddings",
                headers={"Authorization": f"Bearer {config.embedding_api_key}"},
                json={
                    "model": config.embedding_model,
                    "input": texts,
                    "encoding_format": "float",
                },
                timeout=120,
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            embeddings = [item["embedding"] for item in data]
            if len(embeddings) != len(texts):
                raise RuntimeError("embedding response count differs from input count")
            if any(len(embedding) != VECTOR_SIZE for embedding in embeddings):
                raise RuntimeError("embedding response has an unexpected vector size")
            return embeddings
        except Exception as error:
            last_error = error
            if attempt > config.retries:
                break
            time.sleep(2**attempt)
    raise RuntimeError(f"embedding request failed: {last_error}")


def target_filter(hotel_id: str) -> dict[str, Any]:
    return {
        "must": [
            {
                "key": "attributes.target_id",
                "match": {"value": hotel_id},
            },
            {
                "key": "attributes.target_type",
                "match": {"value": TARGET_TYPE},
            },
        ]
    }


def ensure_qdrant_collections(config: Config) -> None:
    collections = {
        TEXT_COLLECTION: {"vectors": {"size": VECTOR_SIZE, "distance": "Cosine"}},
        ENTITY_COLLECTION: {
            "vectors": {
                "description": {"size": VECTOR_SIZE, "distance": "Cosine"},
                "title": {"size": VECTOR_SIZE, "distance": "Cosine"},
            }
        },
    }
    for name, body in collections.items():
        response = requests.get(f"{config.qdrant_url}/collections/{name}", timeout=30)
        if response.status_code == 404:
            create_response = requests.put(
                f"{config.qdrant_url}/collections/{name}",
                json=body,
                timeout=30,
            )
            create_response.raise_for_status()
        else:
            response.raise_for_status()


def replace_qdrant_target(
    config: Config,
    collection: str,
    hotel_id: str,
    points: list[dict[str, Any]],
) -> None:
    delete_response = requests.post(
        f"{config.qdrant_url}/collections/{collection}/points/delete",
        params={"wait": "true"},
        json={"filter": target_filter(hotel_id)},
        timeout=60,
    )
    delete_response.raise_for_status()
    upsert_response = requests.put(
        f"{config.qdrant_url}/collections/{collection}/points",
        params={"wait": "true"},
        json={"points": points},
        timeout=120,
    )
    upsert_response.raise_for_status()


def replace_neo4j_entity(
    config: Config,
    hotel_id: str,
    entity_id: str,
    hotel_name: str,
    description: str,
    snapshot: str,
    review_count: int,
) -> None:
    delete_statement = """
    MATCH (old:Entity {target_id: $target_id, target_type: 'hotel'})
    DETACH DELETE old
    """
    create_statement = """
    CREATE (entity:Entity {
      id: $entity_id,
      readable_id: $target_id,
      title: $title,
      type: 'HOTEL',
      description: $description,
      frequency: $review_count,
      target_id: $target_id,
      target_type: 'hotel',
      review_snapshot: $snapshot
    })
    """
    response = requests.post(
        f"{config.neo4j_url}/db/neo4j/tx/commit",
        auth=(config.neo4j_username, config.neo4j_password),
        json={
            "statements": [
                {
                    "statement": delete_statement,
                    "parameters": {"target_id": hotel_id},
                },
                {
                    "statement": create_statement,
                    "parameters": {
                        "target_id": hotel_id,
                        "entity_id": entity_id,
                        "title": hotel_name,
                        "description": description,
                        "review_count": review_count,
                        "snapshot": snapshot,
                    },
                },
            ]
        },
        timeout=60,
    )
    response.raise_for_status()
    errors = response.json().get("errors") or []
    if errors:
        raise RuntimeError(f"Neo4j write failed: {errors}")


def build_direct_index(
    config: Config,
    hotel: dict[str, Any],
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    if not reviews:
        raise RuntimeError("hotel has no reviews after seeding")
    hotel_id = str(hotel["_id"])
    hotel_name = str(hotel.get("name") or hotel_id)
    snapshot = compute_snapshot(reviews)
    entity_id = str(uuid5(NAMESPACE_URL, f"tripsphere:review-summary:hotel:{hotel_id}"))
    review_texts = [source_text(review) for review in reviews]
    address = hotel.get("address") or {}
    address_text = "".join(
        str(address.get(field) or "") for field in ("city", "district", "detailed")
    )
    tags = [
        str(tag).strip()
        for tag in [*(hotel.get("tags") or []), *(hotel.get("amenities") or [])]
        if str(tag).strip()
    ]
    description_parts = [f"{hotel_name}位于{address_text or '酒店登记地址'}。"]
    if tags:
        description_parts.append(f"酒店资料标签包括{'、'.join(tags)}。")
    description_parts.append(f"当前评论索引包含{len(reviews)}条评论。")
    description = "".join(description_parts)

    embeddings = embed_texts(config, [*review_texts, hotel_name, description])
    review_embeddings = embeddings[: len(review_texts)]
    title_embedding = embeddings[-2]
    description_embedding = embeddings[-1]
    text_unit_ids: list[str] = []
    text_points: list[dict[str, Any]] = []
    for review, text, embedding in zip(
        reviews, review_texts, review_embeddings, strict=True
    ):
        review_id = str(review["_id"])
        text_unit_id = str(
            uuid5(
                NAMESPACE_URL,
                f"tripsphere:review:{TARGET_TYPE}:{hotel_id}:{review_id}",
            )
        )
        text_unit_ids.append(text_unit_id)
        text_points.append(
            {
                "id": text_unit_id,
                "vector": embedding,
                "payload": {
                    "readable_id": review_id,
                    "text": text,
                    "entity_ids": [entity_id],
                    "relationship_ids": [],
                    "n_tokens": max(1, len(text) // 2),
                    "document_id": review_id,
                    "attributes": {
                        "target_id": hotel_id,
                        "target_type": TARGET_TYPE,
                        "review_snapshot": snapshot,
                        "review_id": review_id,
                        "user_id": str(review.get("user_id") or ""),
                        "rating": int(review["rating"]),
                        "updated_at": review_version(review),
                    },
                },
            }
        )

    entity_point = {
        "id": entity_id,
        "vector": {
            "description": description_embedding,
            "title": title_embedding,
        },
        "payload": {
            "readable_id": hotel_id,
            "title": hotel_name,
            "type": "HOTEL",
            "description": description,
            "community_ids": [],
            "text_unit_ids": text_unit_ids,
            "rank": len(reviews),
            "attributes": {
                "target_id": hotel_id,
                "target_type": TARGET_TYPE,
                "review_snapshot": snapshot,
            },
        },
    }

    replace_qdrant_target(config, TEXT_COLLECTION, hotel_id, text_points)
    replace_qdrant_target(config, ENTITY_COLLECTION, hotel_id, [entity_point])
    replace_neo4j_entity(
        config,
        hotel_id,
        entity_id,
        hotel_name,
        description,
        snapshot,
        len(reviews),
    )
    return {
        "snapshot": snapshot,
        "text_units": len(text_points),
        "entities": 1,
        "relationships": 0,
    }


def qdrant_points(
    config: Config, collection: str, hotel_id: str
) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    offset: Any = None
    while True:
        body: dict[str, Any] = {
            "filter": target_filter(hotel_id),
            "limit": 256,
            "with_payload": True,
            "with_vector": False,
        }
        if offset is not None:
            body["offset"] = offset
        response = requests.post(
            f"{config.qdrant_url}/collections/{collection}/points/scroll",
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()["result"]
        points.extend(result.get("points") or [])
        next_offset = result.get("next_page_offset")
        if next_offset is None:
            return points
        if next_offset == offset:
            raise RuntimeError("Qdrant returned a repeated scroll offset")
        offset = next_offset


def neo4j_entities(config: Config, hotel_id: str) -> list[dict[str, Any]]:
    response = requests.post(
        f"{config.neo4j_url}/db/neo4j/tx/commit",
        auth=(config.neo4j_username, config.neo4j_password),
        json={
            "statements": [
                {
                    "statement": (
                        "MATCH (entity:Entity {target_id: $target_id, "
                        "target_type: 'hotel'}) "
                        "RETURN collect({id: entity.id, "
                        "snapshot: entity.review_snapshot})"
                    ),
                    "parameters": {"target_id": hotel_id},
                }
            ]
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"Neo4j verification failed: {payload['errors']}")
    rows = payload.get("results", [{}])[0].get("data", [])
    if len(rows) != 1:
        return []
    return rows[0]["row"][0] or []


def verify_index(
    config: Config,
    hotel_id: str,
    seed_ids: frozenset[str],
    expected: dict[str, Any],
) -> None:
    text_points = qdrant_points(config, TEXT_COLLECTION, hotel_id)
    entity_points = qdrant_points(config, ENTITY_COLLECTION, hotel_id)
    if len(text_points) != expected["text_units"]:
        raise RuntimeError("Qdrant text-unit count differs from the direct build")
    if len(entity_points) != 1:
        raise RuntimeError("Qdrant must contain exactly one hotel entity")

    text_payloads = [point.get("payload") or {} for point in text_points]
    review_ids = {
        str(payload.get("attributes", {}).get("review_id") or "")
        for payload in text_payloads
    }
    if "" in review_ids or len(review_ids) != len(text_points):
        raise RuntimeError("Qdrant contains missing or duplicate review IDs")
    if review_ids != seed_ids:
        raise RuntimeError("MongoDB and Qdrant review IDs differ")
    snapshots = {
        str(payload.get("attributes", {}).get("review_snapshot") or "")
        for payload in text_payloads
    }
    if snapshots != {expected["snapshot"]}:
        raise RuntimeError("Qdrant text units do not share the expected snapshot")
    entity_ids = {str(point["id"]) for point in entity_points}
    referenced_entity_ids = {
        str(entity_id)
        for payload in text_payloads
        for entity_id in (payload.get("entity_ids") or [])
    }
    if referenced_entity_ids != entity_ids:
        raise RuntimeError("text-unit and entity references differ")
    if any(payload.get("relationship_ids") for payload in text_payloads):
        raise RuntimeError("minimal direct index unexpectedly contains relationships")

    entity_snapshot = str(
        (entity_points[0].get("payload") or {})
        .get("attributes", {})
        .get("review_snapshot")
        or ""
    )
    if entity_snapshot != expected["snapshot"]:
        raise RuntimeError("Qdrant entity snapshot differs from text units")
    graph_entities = neo4j_entities(config, hotel_id)
    if {str(entity["id"]) for entity in graph_entities} != entity_ids:
        raise RuntimeError("Neo4j and Qdrant entity IDs differ")
    if any(entity.get("snapshot") != expected["snapshot"] for entity in graph_entities):
        raise RuntimeError("Neo4j entity snapshot differs from Qdrant")


def process_hotel(
    config: Config,
    manifest: Manifest,
    hotel: dict[str, Any],
) -> dict[str, Any]:
    hotel_id = str(hotel["_id"])
    hotel_name = str(hotel.get("name") or hotel_id)
    last_error: Exception | None = None
    for attempt in range(1, config.retries + 2):
        try:
            reviews, seed_ids = seed_and_load_reviews(config, hotel)
            expected = build_direct_index(config, hotel, reviews)
            verify_index(config, hotel_id, seed_ids, expected)
            record = {
                "hotel_id": hotel_id,
                "hotel_name": hotel_name,
                "seed_count": len(seed_ids),
                "status": "index_verified",
                "attempt": attempt,
                **expected,
            }
            manifest.append(record)
            return record
        except Exception as error:
            last_error = error
            manifest.append(
                {
                    "hotel_id": hotel_id,
                    "hotel_name": hotel_name,
                    "status": "attempt_failed",
                    "attempt": attempt,
                    "error": str(error),
                }
            )
            if attempt <= config.retries:
                time.sleep(2 ** (attempt - 1))
    record = {
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "status": "failed",
        "error": str(last_error or "unknown failure"),
    }
    manifest.append(record)
    return record


def print_dry_run(hotels: list[dict[str, Any]], config: Config) -> None:
    counts = [
        stable_review_count(str(hotel["_id"]), config.min_reviews, config.max_reviews)
        for hotel in hotels
    ]
    print(
        json.dumps(
            {
                "mode": "dry-run",
                "strategy": "direct-minimal-pinned-index",
                "hotels": len(hotels),
                "seed_reviews": sum(counts),
                "minimum_per_hotel": min(counts, default=0),
                "maximum_per_hotel": max(counts, default=0),
                "manifest": str(config.manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    for hotel in hotels[:5]:
        reviews = build_seed_reviews(hotel, config.min_reviews, config.max_reviews)
        print(
            json.dumps(
                {
                    "hotel_id": str(hotel["_id"]),
                    "hotel_name": hotel.get("name"),
                    "seed_count": len(reviews),
                    "sample": reviews[0]["content"],
                },
                ensure_ascii=False,
            )
        )


def main() -> int:
    args = parse_args()
    config = build_config(args)
    hotels = load_hotels(config, args.offset, args.limit)
    if not hotels:
        print("No hotels selected.")
        return 0
    if not args.apply:
        print_dry_run(hotels, config)
        return 0

    ensure_qdrant_collections(config)
    manifest = Manifest(config.manifest_path)
    pending = [
        hotel
        for hotel in hotels
        if args.no_resume or not manifest.is_verified(str(hotel["_id"]))
    ]
    skipped = len(hotels) - len(pending)
    print(
        f"Selected {len(hotels)} hotels; pending={len(pending)} "
        f"skipped={skipped}; concurrency={config.concurrency}.",
        flush=True,
    )

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = {
            executor.submit(process_hotel, config, manifest, hotel): hotel
            for hotel in pending
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            hotel = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {
                    "hotel_id": str(hotel["_id"]),
                    "hotel_name": hotel.get("name"),
                    "status": "failed",
                    "error": str(error),
                }
                manifest.append(result)
            results.append(result)
            print(
                f"[{completed}/{len(pending)}] "
                + json.dumps(result, ensure_ascii=False),
                flush=True,
            )

    verified = sum(result.get("status") == "index_verified" for result in results)
    failed = len(results) - verified
    print(
        json.dumps(
            {
                "selected": len(hotels),
                "skipped": skipped,
                "verified": verified,
                "failed": failed,
                "manifest": str(config.manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
