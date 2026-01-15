from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from itinerary.utils.uuid import uuid7


class Activity(BaseModel):
    activity_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    kind: Literal["attraction"] = Field(default="attraction")
    metadata: dict[str, Any] | None = Field(default=None)


class DayPlan(BaseModel):
    day_plan_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    title: str | None = Field(default=None, description="Title of the Day Plan.")
    activities: list[Activity] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class Itinerary(BaseModel):
    itinerary_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    title: str | None = Field(default=None, description="Title of the Itinerary.")
    user_id: str = Field(..., description="ID of the User who owns the Itinerary.")
    day_plans: list[DayPlan] = Field(
        default_factory=lambda: [DayPlan()],
        description="List of day plans in the Itinerary.",
    )
    start_date: date = Field(..., description="Start date of the Itinerary.")
    end_date: date = Field(..., description="End date of the Itinerary.")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)
