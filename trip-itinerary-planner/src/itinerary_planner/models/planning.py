from enum import StrEnum

from pydantic import BaseModel, Field

from itinerary_planner.models.itinerary import Itinerary


class PlanningStep(StrEnum):
    ANALYZING_PREFERENCES = "analyzing_preferences"
    RESEARCHING_DESTINATION = "researching_destination"
    FINDING_ATTRACTIONS = "finding_attractions"
    OPTIMIZING_ROUTE = "optimizing_route"
    FINALIZING = "finalizing"


class PlanningProgressEvent(BaseModel):
    progress_percentage: int = Field(
        ge=0, le=100, description="Progress percentage (0-100)"
    )
    status_message: str = Field(description="Human-readable status message")
    current_step: str = Field(description="Current planning step")
    itinerary: Itinerary | None = Field(
        default=None, description="Final itinerary (only in the last event)"
    )
