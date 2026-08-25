from datetime import time
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

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
    current_step: PlanningStep = Field(description="Current planning step")
    itinerary: Itinerary | None = Field(
        default=None, description="Final itinerary (only in the last event)"
    )


class GeneratedActivity(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    estimated_cost: float = Field(ge=0)

    @field_validator("name", "description", "category")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        try:
            start = time.fromisoformat(self.start_time)
            end = time.fromisoformat(self.end_time)
        except ValueError as exc:
            raise ValueError("activity times must use HH:MM format") from exc
        if start >= end:
            raise ValueError("activity end time must be after start time")
        return self


class GeneratedDayPlan(BaseModel):
    day_number: int = Field(ge=1)
    activities: list[GeneratedActivity] = Field(min_length=1)
    notes: str = ""


class GeneratedItineraryPlan(BaseModel):
    destination_info: str = Field(min_length=1)
    day_plans: list[GeneratedDayPlan] = Field(min_length=1)
    highlights: list[str]
    total_estimated_cost: float = Field(ge=0)
