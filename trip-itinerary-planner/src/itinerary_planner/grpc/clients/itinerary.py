"""gRPC client for trip-itinerary-service.

Converts between the planner's Pydantic models and the itinerary service
proto messages, then performs RPC calls.  All I/O is async (grpc.aio).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import grpc
from tripsphere.attraction.v1 import attraction_pb2
from tripsphere.common.v1 import date_pb2, map_pb2, money_pb2, timeofday_pb2
from tripsphere.hotel.v1 import hotel_pb2
from tripsphere.itinerary.v1 import itinerary_pb2, itinerary_pb2_grpc

from itinerary_planner.models.activity import Activity, ActivityLocation, Cost
from itinerary_planner.models.itinerary import DayPlan, Itinerary, ItinerarySummary

if TYPE_CHECKING:
    from itinerary_planner.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)

# Default gRPC port when metadata is missing (e.g. legacy instance)
_DEFAULT_GRPC_PORT = 50052

# ── Kind string → proto enum ────────────────────────────────────────────────

_KIND_TO_PROTO: dict[str, itinerary_pb2.ActivityKind.ValueType] = {
    "attraction_visit": itinerary_pb2.ACTIVITY_KIND_ATTRACTION_VISIT,
    "dining": itinerary_pb2.ACTIVITY_KIND_DINING,
    "hotel_stay": itinerary_pb2.ACTIVITY_KIND_HOTEL_STAY,
    "custom": itinerary_pb2.ACTIVITY_KIND_CUSTOM,
}

_PROTO_TO_KIND: dict[itinerary_pb2.ActivityKind.ValueType, str] = {
    v: k for k, v in _KIND_TO_PROTO.items()
}


# ── Planner model → proto converters ────────────────────────────────────────


def _parse_time(hhmm: str) -> timeofday_pb2.TimeOfDay:
    parts = hhmm.split(":")
    h = int(parts[0]) if parts else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    return timeofday_pb2.TimeOfDay(hours=h, minutes=m)


def _parse_date(iso: str) -> date_pb2.Date:
    d = datetime.fromisoformat(iso).date()
    return date_pb2.Date(year=d.year, month=d.month, day=d.day)


def _activity_to_proto(activity: Activity) -> itinerary_pb2.Activity:
    kwargs: dict[str, Any] = {
        "id": activity.id,
        "title": activity.name,
        "description": activity.description,
        "kind": _KIND_TO_PROTO.get(
            activity.kind, itinerary_pb2.ACTIVITY_KIND_UNSPECIFIED
        ),
        "start_time": _parse_time(activity.start_time),
        "end_time": _parse_time(activity.end_time),
        "estimated_cost": money_pb2.Money(
            currency=activity.estimated_cost.currency,
            units=int(activity.estimated_cost.amount),
            nanos=int((activity.estimated_cost.amount % 1) * 1_000_000_000),
        ),
        "location": map_pb2.GeoPoint(
            longitude=activity.location.longitude,
            latitude=activity.location.latitude,
        ),
        "address": map_pb2.Address(detailed=activity.location.address or ""),
        "category": activity.category,
    }
    # oneof resource: attraction or hotel
    if activity.attraction_id:
        kwargs["attraction"] = attraction_pb2.Attraction(id=activity.attraction_id)
    elif activity.hotel_id:
        kwargs["hotel"] = hotel_pb2.Hotel(id=activity.hotel_id)
    return itinerary_pb2.Activity(**kwargs)


def _day_plan_to_proto(day_plan: DayPlan) -> itinerary_pb2.DayPlan:
    return itinerary_pb2.DayPlan(
        date=_parse_date(day_plan.date),
        day_number=day_plan.day_number,
        notes=day_plan.notes,
        activities=[_activity_to_proto(a) for a in day_plan.activities],
    )


def _summary_to_proto(s: ItinerarySummary) -> itinerary_pb2.ItinerarySummary:
    """Build proto ItinerarySummary using Money for total_estimated_cost."""
    amount = s.total_estimated_cost
    units = int(amount)
    nanos = int(round((amount % 1) * 1_000_000_000))
    return itinerary_pb2.ItinerarySummary(
        total_estimated_cost=money_pb2.Money(
            currency=s.currency or "CNY",
            units=units,
            nanos=nanos,
        ),
        total_activities=s.total_activities,
        highlights=s.highlights,
    )


def _itinerary_to_proto(
    itinerary: Itinerary, markdown_content: str = ""
) -> itinerary_pb2.Itinerary:
    summary = None
    if itinerary.summary is not None:
        summary = _summary_to_proto(itinerary.summary)

    return itinerary_pb2.Itinerary(
        title=itinerary.destination,  # use destination as title when no separate title
        destination_name=itinerary.destination,
        start_date=_parse_date(itinerary.start_date),
        end_date=_parse_date(itinerary.end_date),
        day_plans=[_day_plan_to_proto(dp) for dp in itinerary.day_plans],
        summary=summary,
        markdown_content=markdown_content,
    )


# ── Proto → planner model converters ────────────────────────────────────────


def _time_to_str(t: timeofday_pb2.TimeOfDay) -> str:
    return f"{t.hours:02d}:{t.minutes:02d}"


def _date_to_str(d: date_pb2.Date) -> str:
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def _format_address(addr: map_pb2.Address) -> str:
    parts = [addr.province, addr.city, addr.district, addr.detailed]
    return "".join(p for p in parts if p)


def _proto_to_activity(proto: itinerary_pb2.Activity) -> Activity:
    lat = 0.0
    lng = 0.0
    if proto.HasField("location"):
        lat = proto.location.latitude
        lng = proto.location.longitude
    line_address = ""
    if proto.HasField("address"):
        line_address = _format_address(proto.address)
    location = ActivityLocation(
        name=proto.title or "",
        latitude=lat,
        longitude=lng,
        address=line_address,
    )

    amount = proto.estimated_cost.units + proto.estimated_cost.nanos / 1_000_000_000
    cost = Cost(amount=amount, currency=proto.estimated_cost.currency or "CNY")

    attraction_id: str | None = None
    hotel_id: str | None = None
    resource = proto.WhichOneof("resource")
    if resource == "attraction":
        attraction_id = proto.attraction.id or None
    elif resource == "hotel":
        hotel_id = proto.hotel.id or None

    return Activity(
        id=proto.id,
        name=proto.title,
        description=proto.description,
        start_time=_time_to_str(proto.start_time),
        end_time=_time_to_str(proto.end_time),
        location=location,
        category=proto.category or "sightseeing",
        estimated_cost=cost,
        kind=_PROTO_TO_KIND.get(proto.kind, "attraction_visit"),
        attraction_id=attraction_id,
        hotel_id=hotel_id,
    )


def _proto_to_day_plan(proto: itinerary_pb2.DayPlan) -> DayPlan:
    return DayPlan(
        day_number=proto.day_number,
        date=_date_to_str(proto.date),
        notes=proto.notes,
        activities=[_proto_to_activity(a) for a in proto.activities],
    )


def _proto_to_summary(
    proto_summary: itinerary_pb2.ItinerarySummary,
) -> ItinerarySummary:
    """Extract Pydantic ItinerarySummary from proto (Money -> amount + currency)."""
    cost = proto_summary.total_estimated_cost
    amount = cost.units + cost.nanos / 1_000_000_000 if cost else 0.0
    currency = cost.currency or "CNY" if cost else "CNY"
    return ItinerarySummary(
        total_estimated_cost=amount,
        currency=currency,
        total_activities=proto_summary.total_activities,
        highlights=list(proto_summary.highlights),
    )


def _proto_to_itinerary(proto: itinerary_pb2.Itinerary) -> tuple[Itinerary, str]:
    """Returns (Itinerary, markdown_content)."""
    summary: ItinerarySummary | None = None
    if proto.HasField("summary"):
        summary = _proto_to_summary(proto.summary)

    itinerary = Itinerary(
        id=proto.id,
        destination=proto.destination_name or proto.title,
        start_date=_date_to_str(proto.start_date),
        end_date=_date_to_str(proto.end_date),
        day_plans=[_proto_to_day_plan(dp) for dp in proto.day_plans],
        summary=summary,
    )
    return itinerary, proto.markdown_content


def _proto_to_itinerary_summary(proto: itinerary_pb2.Itinerary) -> dict:  # type: ignore[type-arg]
    """Convert a proto Itinerary to the summary dict used by the list endpoint."""
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    if proto.HasField("created_at"):
        created_at = datetime.fromtimestamp(
            proto.created_at.seconds + proto.created_at.nanos / 1e9, tz=timezone.utc
        )
    if proto.HasField("updated_at"):
        updated_at = datetime.fromtimestamp(
            proto.updated_at.seconds + proto.updated_at.nanos / 1e9, tz=timezone.utc
        )
    return {
        "id": proto.id,
        "destination": proto.destination_name or proto.title,
        "start_date": _date_to_str(proto.start_date),
        "end_date": _date_to_str(proto.end_date),
        "day_count": len(proto.day_plans),
        "created_at": created_at,
        "updated_at": updated_at,
    }


# ── Client ──────────────────────────────────────────────────────────────────


class ItineraryServiceClient:
    """Async gRPC client wrapper around trip-itinerary-service.
    Resolves target via Nacos service discovery (per-request).
    """

    def __init__(
        self,
        nacos_naming: "NacosNaming",
        service_name: str = "trip-itinerary-service",
    ) -> None:
        self._nacos_naming = nacos_naming
        self._service_name = service_name

    async def _resolve_address(self) -> str:
        instance = await self._nacos_naming.get_service_instance(self._service_name)
        port_str = (instance.metadata or {}).get("gRPC_port", str(_DEFAULT_GRPC_PORT))
        port = int(port_str)
        return f"{instance.ip}:{port}"

    async def create_itinerary(
        self,
        itinerary: Itinerary,
        user_id: str,
        markdown_content: str = "",
    ) -> Itinerary:
        """Create the itinerary via gRPC.
        The server overwrites user_id from auth metadata.
        """
        proto = _itinerary_to_proto(itinerary, markdown_content)
        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
            # x-user-id is read by AuthInterceptor to populate GrpcAuthContext
            metadata = [("x-user-id", user_id)]
            response = await stub.CreateItinerary(
                itinerary_pb2.CreateItineraryRequest(itinerary=proto),
                metadata=metadata,
            )
        saved, _ = _proto_to_itinerary(response.itinerary)
        return saved.model_copy(update={"id": response.itinerary.id})

    async def get_itinerary(
        self, itinerary_id: str, user_id: str
    ) -> tuple[Itinerary, str]:
        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
            metadata = [("x-user-id", user_id)]
            response = await stub.GetItinerary(
                itinerary_pb2.GetItineraryRequest(id=itinerary_id),
                metadata=metadata,
            )
        return _proto_to_itinerary(response.itinerary)

    async def list_user_itineraries(
        self, user_id: str, page_size: int = 50
    ) -> list[dict]:  # type: ignore[type-arg]
        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
            metadata = [("x-user-id", user_id)]
            response = await stub.ListUserItineraries(
                itinerary_pb2.ListUserItinerariesRequest(
                    user_id=user_id, page_size=page_size
                ),
                metadata=metadata,
            )
        return [_proto_to_itinerary_summary(it) for it in response.itineraries]

    async def replace_itinerary(
        self,
        itinerary_id: str,
        itinerary: Itinerary,
        user_id: str,
        markdown_content: str = "",
    ) -> Itinerary:
        proto = _itinerary_to_proto(itinerary, markdown_content)
        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
            metadata = [("x-user-id", user_id)]
            response = await stub.ReplaceItinerary(
                itinerary_pb2.ReplaceItineraryRequest(id=itinerary_id, itinerary=proto),
                metadata=metadata,
            )
        saved, _ = _proto_to_itinerary(response.itinerary)
        return saved.model_copy(update={"id": response.itinerary.id})

    async def delete_itinerary(self, itinerary_id: str, user_id: str) -> None:
        address = await self._resolve_address()
        async with grpc.aio.insecure_channel(address) as channel:
            stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
            metadata = [("x-user-id", user_id)]
            await stub.DeleteItinerary(
                itinerary_pb2.DeleteItineraryRequest(id=itinerary_id),
                metadata=metadata,
            )
