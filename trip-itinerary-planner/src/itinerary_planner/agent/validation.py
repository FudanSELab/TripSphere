from datetime import date, time, timedelta
from math import isfinite

from itinerary_planner.agent.exceptions import InvalidPlanningResultError
from itinerary_planner.models.itinerary import Itinerary
from itinerary_planner.models.planning import GeneratedItineraryPlan


def coordinates_are_valid(longitude: float, latitude: float) -> bool:
    return (
        isfinite(longitude)
        and isfinite(latitude)
        and -180 <= longitude <= 180
        and -90 <= latitude <= 90
        and (longitude != 0 or latitude != 0)
    )


def validate_generated_plan(
    plan: GeneratedItineraryPlan,
    expected_day_count: int,
) -> None:
    expected_day_numbers = list(range(1, expected_day_count + 1))
    actual_day_numbers = sorted(day.day_number for day in plan.day_plans)
    if actual_day_numbers != expected_day_numbers:
        raise InvalidPlanningResultError(
            "Generated itinerary must contain exactly one plan for each trip day"
        )


def validate_itinerary(
    itinerary: Itinerary,
    valid_attraction_ids: set[str],
    valid_hotel_ids: set[str],
) -> None:
    if not itinerary.id.strip() or not itinerary.destination.strip():
        raise InvalidPlanningResultError(
            "Generated itinerary is missing its id or destination"
        )

    start_date = date.fromisoformat(itinerary.start_date)
    end_date = date.fromisoformat(itinerary.end_date)
    if end_date < start_date:
        raise InvalidPlanningResultError(
            "Generated itinerary end date is before its start date"
        )
    expected_day_count = (end_date - start_date).days + 1

    if len(itinerary.day_plans) != expected_day_count:
        raise InvalidPlanningResultError(
            "Generated itinerary day count does not match the requested dates"
        )

    activity_ids: set[str] = set()
    for index, day_plan in enumerate(itinerary.day_plans):
        expected_day_number = index + 1
        expected_date = (start_date + timedelta(days=index)).isoformat()
        if day_plan.day_number != expected_day_number or day_plan.date != expected_date:
            raise InvalidPlanningResultError(
                "Generated itinerary contains an invalid day number or date"
            )
        if not day_plan.activities:
            raise InvalidPlanningResultError(
                f"Generated itinerary day {expected_day_number} has no activities"
            )

        for activity in day_plan.activities:
            if (
                not activity.id.strip()
                or not activity.name.strip()
                or activity.id in activity_ids
            ):
                raise InvalidPlanningResultError(
                    "Generated itinerary contains a missing name or invalid activity id"
                )
            activity_ids.add(activity.id)

            try:
                start_time = time.fromisoformat(activity.start_time)
                end_time = time.fromisoformat(activity.end_time)
            except ValueError as exc:
                raise InvalidPlanningResultError(
                    f"Activity '{activity.name}' contains an invalid time"
                ) from exc
            if activity.kind != "hotel_stay" and start_time >= end_time:
                raise InvalidPlanningResultError(
                    f"Activity '{activity.name}' contains an invalid time range"
                )

            if (
                not isfinite(activity.estimated_cost.amount)
                or activity.estimated_cost.amount < 0
            ):
                raise InvalidPlanningResultError(
                    f"Activity '{activity.name}' contains an invalid estimated cost"
                )

            if not coordinates_are_valid(
                activity.location.longitude,
                activity.location.latitude,
            ):
                raise InvalidPlanningResultError(
                    f"Activity '{activity.name}' contains invalid coordinates"
                )

            if activity.attraction_id:
                if activity.attraction_id not in valid_attraction_ids:
                    raise InvalidPlanningResultError(
                        f"Activity '{activity.name}' references an unknown attraction"
                    )
                if activity.kind != "attraction_visit":
                    raise InvalidPlanningResultError(
                        f"Activity '{activity.name}' has an invalid attraction kind"
                    )

            if activity.hotel_id:
                if activity.hotel_id not in valid_hotel_ids:
                    raise InvalidPlanningResultError(
                        f"Activity '{activity.name}' references an unknown hotel"
                    )
                if activity.kind != "hotel_stay":
                    raise InvalidPlanningResultError(
                        f"Activity '{activity.name}' has an invalid hotel kind"
                    )

            if activity.attraction_id and activity.hotel_id:
                raise InvalidPlanningResultError(
                    f"Activity '{activity.name}' references multiple entities"
                )

            if activity.kind == "attraction_visit" and not activity.attraction_id:
                raise InvalidPlanningResultError(
                    f"Attraction activity '{activity.name}' is missing an attraction id"
                )
            if activity.kind == "hotel_stay" and not activity.hotel_id:
                raise InvalidPlanningResultError(
                    f"Hotel activity '{activity.name}' is missing a hotel id"
                )
