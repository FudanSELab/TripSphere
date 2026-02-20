import logging

import grpc
from tripsphere.common.v1 import date_pb2, money_pb2, timeofday_pb2  # pyright: ignore
from tripsphere.itinerary.v1 import itinerary_pb2, itinerary_pb2_grpc  # pyright: ignore

from itinerary_planner.models.activity import Activity
from itinerary_planner.models.itinerary import DayPlan, Itinerary
from itinerary_planner.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)

_KIND_MAP: dict[str, itinerary_pb2.ActivityKind.ValueType] = {
    "attraction_visit": itinerary_pb2.ACTIVITY_KIND_ATTRACTION_VISIT,
    "dining": itinerary_pb2.ACTIVITY_KIND_DINING,
    "hotel_stay": itinerary_pb2.ACTIVITY_KIND_HOTEL_STAY,
}


def _parse_date(date_str: str) -> date_pb2.Date:
    """Parse 'YYYY-MM-DD' string to proto Date."""
    year, month, day = date_str.split("-")
    return date_pb2.Date(year=int(year), month=int(month), day=int(day))


def _parse_time(time_str: str) -> timeofday_pb2.TimeOfDay:
    """Parse 'HH:MM' string to proto TimeOfDay."""
    parts = time_str.split(":")
    return timeofday_pb2.TimeOfDay(hours=int(parts[0]), minutes=int(parts[1]))


def _parse_money(amount: float, currency: str) -> money_pb2.Money:
    """Convert a float amount to proto Money (whole units + nanoseconds remainder)."""
    units = int(amount)
    nanos = round((amount - units) * 1_000_000_000)
    return money_pb2.Money(currency=currency, units=units, nanos=nanos)


def _to_proto_activity(activity: Activity) -> itinerary_pb2.Activity:
    kind = _KIND_MAP.get(activity.kind, itinerary_pb2.ACTIVITY_KIND_CUSTOM)
    return itinerary_pb2.Activity(
        title=activity.name,
        description=activity.description,
        kind=kind,
        start_time=_parse_time(activity.start_time),
        end_time=_parse_time(activity.end_time),
        estimated_cost=_parse_money(
            activity.estimated_cost.amount,
            activity.estimated_cost.currency,
        ),
    )


def _to_proto_day_plan(day_plan: DayPlan) -> itinerary_pb2.DayPlan:
    return itinerary_pb2.DayPlan(
        date=_parse_date(day_plan.date),
        title=f"Day {day_plan.day_number}",
        notes=day_plan.notes,
        activities=[_to_proto_activity(a) for a in day_plan.activities],
    )


def _to_proto_itinerary(itinerary: Itinerary, user_id: str) -> itinerary_pb2.Itinerary:
    return itinerary_pb2.Itinerary(
        title=itinerary.destination,
        user_id=user_id,
        start_date=_parse_date(itinerary.start_date),
        end_date=_parse_date(itinerary.end_date),
        day_plans=[_to_proto_day_plan(dp) for dp in itinerary.day_plans],
    )


async def save_itinerary(
    nacos_naming: NacosNaming,
    user_id: str,
    itinerary: Itinerary,
) -> Itinerary:
    """Persist a planned itinerary to trip-itinerary-service via gRPC.

    On success, returns the itinerary with the server-assigned ID replacing
    the client-generated UUID.  On failure, logs the error and returns the
    original itinerary unchanged so the caller still gets a result.
    """
    try:
        instance = await nacos_naming.get_service_instance("trip-itinerary-service")
        address = f"{instance.ip}:{instance.metadata['gRPC_port']}"  # pyright: ignore

        proto_itinerary = _to_proto_itinerary(itinerary, user_id)
        request = itinerary_pb2.CreateItineraryRequest(itinerary=proto_itinerary)

        # The service reads identity from these metadata headers (set by the BFF).
        # Roles must include USER so requireAuthenticated() passes.
        metadata = (
            ("x-user-id", user_id),
            ("x-user-roles", "USER"),
        )

        async with grpc.aio.insecure_channel(address) as channel:
            stub: itinerary_pb2_grpc.ItineraryServiceAsyncStub = (
                itinerary_pb2_grpc.ItineraryServiceStub(channel)  # pyright: ignore
            )
            response = await stub.CreateItinerary(request, metadata=metadata)

        saved_id: str = response.itinerary.id
        logger.info("Itinerary persisted to trip-itinerary-service (id=%s)", saved_id)
        return itinerary.model_copy(update={"id": saved_id})

    except Exception:
        logger.exception(
            "Failed to persist itinerary to trip-itinerary-service; "
            "returning unsaved itinerary"
        )
        return itinerary
