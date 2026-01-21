from pydantic import BaseModel, Field

from itinerary_planner.models.itinerary import Itinerary


class PlanningProgressEvent(BaseModel):
    progress_percentage: int = Field(
        ge=0, le=100, description="Progress percentage (0-100)"
    )
    status_message: str = Field(description="Human-readable status message")
    current_step: str = Field(description="Current planning step")
    itinerary: Itinerary | None = Field(
        default=None, description="Final itinerary (only in the last event)"
    )
