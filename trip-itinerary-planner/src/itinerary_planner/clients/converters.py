"""Convert Pydantic itinerary models to protobuf messages for gRPC persistence."""

from tripsphere.common.v1 import date_pb2, money_pb2, timeofday_pb2  # pyright: ignore
from tripsphere.itinerary.v1 import itinerary_pb2  # pyright: ignore
from tripsphere.poi.v1 import poi_pb2  # pyright: ignore

from itinerary_planner.models.activity import Activity, Cost
from itinerary_planner.models.itinerary import DayPlan, Itinerary

_KIND_MAP: dict[str, itinerary_pb2.ActivityKind.ValueType] = {
    "attraction_visit": itinerary_pb2.ACTIVITY_KIND_ATTRACTION_VISIT,
    "dining": itinerary_pb2.ACTIVITY_KIND_DINING,
    "hotel_stay": itinerary_pb2.ACTIVITY_KIND_HOTEL_STAY,
    "custom": itinerary_pb2.ACTIVITY_KIND_CUSTOM,
}


def itinerary_to_proto(itinerary: Itinerary) -> itinerary_pb2.Itinerary:
    """Convert a Pydantic Itinerary to the protobuf Itinerary message."""
    destination_poi = poi_pb2.Poi(name=itinerary.destination)

    return itinerary_pb2.Itinerary(
        title=f"{itinerary.destination} Trip",
        destination=destination_poi,
        start_date=_parse_date(itinerary.start_date),
        end_date=_parse_date(itinerary.end_date),
        day_plans=[_day_plan_to_proto(dp) for dp in itinerary.day_plans],
    )


def _day_plan_to_proto(day_plan: DayPlan) -> itinerary_pb2.DayPlan:
    return itinerary_pb2.DayPlan(
        date=_parse_date(day_plan.date),
        title=f"Day {day_plan.day_number}",
        activities=[_activity_to_proto(a) for a in day_plan.activities],
        notes=day_plan.notes,
    )


def _activity_to_proto(activity: Activity) -> itinerary_pb2.Activity:
    return itinerary_pb2.Activity(
        kind=_activity_kind_to_proto(activity.kind),
        title=activity.name,
        description=activity.description,
        start_time=_parse_time(activity.start_time),
        end_time=_parse_time(activity.end_time),
        estimated_cost=_cost_to_money(activity.estimated_cost),
    )


def _parse_date(date_str: str) -> date_pb2.Date:
    """Parse 'YYYY-MM-DD' into a protobuf Date."""
    parts = date_str.split("-")
    return date_pb2.Date(
        year=int(parts[0]),
        month=int(parts[1]),
        day=int(parts[2]),
    )


def _parse_time(time_str: str) -> timeofday_pb2.TimeOfDay:
    """Parse 'HH:MM' or 'HH:MM:SS' into a protobuf TimeOfDay."""
    parts = time_str.split(":")
    return timeofday_pb2.TimeOfDay(
        hours=int(parts[0]),
        minutes=int(parts[1]),
        seconds=int(parts[2]) if len(parts) > 2 else 0,
    )


def _cost_to_money(cost: Cost) -> money_pb2.Money:
    """Convert a Cost (float amount + currency) to protobuf Money (units + nanos)."""
    units = int(cost.amount)
    nanos = int(round((cost.amount - units) * 1_000_000_000))
    if cost.amount < 0 and nanos > 0:
        nanos = -nanos
    return money_pb2.Money(currency=cost.currency, units=units, nanos=nanos)


def _activity_kind_to_proto(
    kind: str,
) -> itinerary_pb2.ActivityKind.ValueType:
    return _KIND_MAP.get(kind, itinerary_pb2.ACTIVITY_KIND_CUSTOM)
