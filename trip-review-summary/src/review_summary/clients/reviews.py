from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import grpc
from tripsphere.review.v1 import review_pb2, review_pb2_grpc

from review_summary.infra.nacos.naming import NacosNaming


class TargetType(StrEnum):
    HOTEL = "hotel"
    ATTRACTION = "attraction"


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    id: str
    user_id: str
    target_id: str
    target_type: TargetType
    rating: int
    content: str
    updated_at: str


class ReviewServiceClient:
    _PAGE_SIZE = 100
    _REQUEST_TIMEOUT_SECONDS = 10.0

    def __init__(
        self,
        naming: NacosNaming,
        service_name: str = "trip-review-service",
    ) -> None:
        self._naming = naming
        self._service_name = service_name

    async def list_all(
        self, target_id: str, target_type: TargetType
    ) -> list[ReviewRecord]:
        if not target_id:
            raise ValueError("target_id must not be empty")

        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = review_pb2_grpc.ReviewServiceStub(channel)
            return await self._list_all_pages(stub, target_id, target_type)

    async def _resolve_address(self) -> str:
        instance = await self._naming.get_service_instance(
            self._service_name,
            required_metadata=("gRPC_port",),
        )
        raw_port = (instance.metadata or {}).get("gRPC_port")
        try:
            port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"{self._service_name} instance has an invalid gRPC_port"
            ) from exc
        if not 1 <= port <= 65535:
            raise RuntimeError(
                f"{self._service_name} instance has an invalid gRPC_port"
            )
        return f"{instance.ip}:{port}"

    async def _list_all_pages(
        self,
        stub: review_pb2_grpc.ReviewServiceStub,
        target_id: str,
        target_type: TargetType,
    ) -> list[ReviewRecord]:
        records: list[ReviewRecord] = []
        page_token = ""
        requested_tokens: set[str] = set()
        entity_type = _to_proto_target_type(target_type)

        while True:
            if page_token in requested_tokens:
                raise RuntimeError("ReviewService returned a repeated page token")
            requested_tokens.add(page_token)

            response = await stub.ListReviewsByEntity(
                review_pb2.ListReviewsByEntityRequest(
                    entity_type=entity_type,
                    entity_id=target_id,
                    page_size=self._PAGE_SIZE,
                    page_token=page_token,
                ),
                timeout=self._REQUEST_TIMEOUT_SECONDS,
            )
            records.extend(
                _to_review_record(review, target_id, target_type)
                for review in response.reviews
            )

            next_page_token = response.next_page_token
            if not next_page_token:
                return records
            if next_page_token in requested_tokens:
                raise RuntimeError("ReviewService returned a repeated page token")
            page_token = next_page_token


def _to_proto_target_type(target_type: TargetType) -> int:
    match target_type:
        case TargetType.HOTEL:
            return review_pb2.ENTITY_TYPE_HOTEL
        case TargetType.ATTRACTION:
            return review_pb2.ENTITY_TYPE_ATTRACTION
    raise ValueError(f"Unsupported target type: {target_type}")


def _to_review_record(
    review: review_pb2.Review,
    target_id: str,
    target_type: TargetType,
) -> ReviewRecord:
    if review.entity_id != target_id:
        raise RuntimeError(
            f"ReviewService returned review {review.id!r} for another target"
        )
    if review.entity_type != _to_proto_target_type(target_type):
        raise RuntimeError(
            f"ReviewService returned review {review.id!r} with another target type"
        )

    updated_at = review.updated_at
    return ReviewRecord(
        id=review.id,
        user_id=review.user_id,
        target_id=review.entity_id,
        target_type=target_type,
        rating=review.rating,
        content=review.content,
        updated_at=f"{updated_at.seconds}:{updated_at.nanos:09d}",
    )
