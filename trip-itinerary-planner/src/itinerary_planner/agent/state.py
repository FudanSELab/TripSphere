from operator import add
from typing import Annotated, Any, TypedDict

from itinerary_planner.models.activity import ActivitySuggestion
from itinerary_planner.models.itinerary import Itinerary, TravelInterest, TripPace
from itinerary_planner.models.planning import PlanningProgressEvent
from itinerary_planner.nacos.naming import NacosNaming


class PlanningState(TypedDict):
    # Nacos naming service instance
    nacos_naming: NacosNaming

    # Input parameters
    user_id: str
    destination: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    interests: list[TravelInterest]
    pace: TripPace
    additional_preferences: str

    # Working data accumulated through workflow
    destination_info: str  # Research results from LLM
    destination_coords: dict[str, Any]  # {latitude, longitude, address}
    activity_suggestions: list[ActivitySuggestion]  # Generated activities
    attraction_details: dict[str, dict[str, Any]]
    daily_schedule: dict[int, list[dict[str, Any]]]  # Day number -> activities

    # Output
    itinerary: Itinerary | None
    error: str | None

    # Streaming events (accumulated using operator.add)
    events: Annotated[list[PlanningProgressEvent], add]
