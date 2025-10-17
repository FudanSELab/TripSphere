"""State definitions for the itinerary planning workflow."""

from typing import Any, TypedDict


class ItineraryState(TypedDict):
    """State object for the itinerary planning workflow."""

    # Input fields
    user_id: str
    destination: str
    start_date: str
    end_date: str
    interests: list[str]
    budget_level: str
    num_travelers: int
    preferences: dict[str, str]

    # Planning state
    destination_info: str
    activity_suggestions: list[dict[str, Any]]
    daily_schedule: dict[int, list[dict[str, Any]]]

    # Output fields
    itinerary: dict[str, Any]
    error: str | None

