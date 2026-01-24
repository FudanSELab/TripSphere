from enum import StrEnum

from pydantic import BaseModel, Field

from itinerary_planner.models.activity import Activity


class TripPace(StrEnum):
    RELAXED = "relaxed"
    MODERATE = "moderate"
    INTENSE = "intense"


class TravelInterest(StrEnum):
    CULTURE = "culture"
    CLASSIC = "classic"
    NATURE = "nature"
    CITYSCAPE = "cityscape"
    HISTORY = "history"


class DayPlan(BaseModel):
    day_number: int = Field(description="Day number (1-indexed)")
    date: str = Field(description="Date in YYYY-MM-DD format")
    activities: list[Activity] = Field(
        default_factory=list[Activity], description="List of activities for the day"
    )
    notes: str = Field(default="", description="Additional notes for the day")


class ItinerarySummary(BaseModel):
    total_estimated_cost: float = Field(description="Total estimated cost")
    currency: str = Field(default="CNY", description="Currency code")
    total_activities: int = Field(description="Total number of activities")
    highlights: list[str] = Field(
        default_factory=list, description="Key highlights of the trip"
    )


class Itinerary(BaseModel):
    id: str = Field(description="Unique itinerary identifier")
    destination: str = Field(description="Destination name")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    day_plans: list[DayPlan] = Field(
        default_factory=list[DayPlan], description="Daily plans"
    )
    summary: ItinerarySummary = Field(description="Trip summary")
