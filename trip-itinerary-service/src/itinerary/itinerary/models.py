import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from itinerary.utils.uuid import uuid7


class BudgetLevel(str, Enum):
    UNSPECIFIED = "unspecified"
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class Coordinates(BaseModel):
    longitude: float = Field(default=0.0, description="Longitude")
    latitude: float = Field(default=0.0, description="Latitude")


class ActivityLocation(BaseModel):
    name: str = Field(default="", description="Location name")
    coordinates: Coordinates = Field(
        default_factory=Coordinates, description="Geographic coordinates"
    )
    address: str = Field(default="", description="Address")


class Cost(BaseModel):
    amount: float = Field(default=0.0, description="Cost amount")
    currency: str = Field(default="CNY", description="Currency code (ISO 4217)")


class Activity(BaseModel):
    activity_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    kind: str = Field(
        default="attraction_visit",
        description="Activity kind: attraction_visit, dining, "
        "hotel_stay, transport, custom",
    )
    # Basic information
    name: str = Field(default="", description="Activity name")
    description: str = Field(default="", description="Activity description")
    # Time information
    start_time: str = Field(default="", description="Start time (HH:MM)")
    end_time: str = Field(default="", description="End time (HH:MM)")
    # Location information
    location: ActivityLocation = Field(
        default_factory=ActivityLocation, description="Location info"
    )
    # Category
    category: str = Field(
        default="sightseeing",
        description="Category: sightseeing, dining, shopping, entertainment, etc.",
    )
    # Cost
    cost: Cost = Field(default_factory=Cost, description="Cost information")
    # Resource associations
    attraction_id: str | None = Field(
        default=None, description="Associated attraction ID"
    )
    hotel_id: str | None = Field(default=None, description="Associated hotel ID")
    # Extension fields
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class DayPlan(BaseModel):
    day_plan_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    day_number: int = Field(default=1, description="Day number")
    date: datetime.date | None = Field(default=None, description="Date of the day plan")
    title: str = Field(default="", description="Title of the Day Plan")
    activities: list[Activity] = Field(
        default_factory=list[Activity], description="List of activities"
    )
    notes: str = Field(default="", description="Notes for the day")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class ItinerarySummary(BaseModel):
    total_estimated_cost: float = Field(default=0.0, description="Total estimated cost")
    currency: str = Field(default="CNY", description="Currency code")
    total_activities: int = Field(default=0, description="Total number of activities")
    highlights: list[str] = Field(default_factory=list, description="Trip highlights")


class Itinerary(BaseModel):
    itinerary_id: str = Field(alias="_id", default_factory=lambda: str(uuid7()))
    title: str = Field(default="", description="Title of the Itinerary")
    user_id: str = Field(..., description="ID of the User who owns the Itinerary")

    # Destination information
    destination: str = Field(default="", description="Destination")

    # Dates
    start_date: datetime.date = Field(..., description="Start date of the Itinerary")
    end_date: datetime.date = Field(..., description="End date of the Itinerary")

    # Daily schedule
    day_plans: list[DayPlan] = Field(
        default_factory=list[DayPlan],
        description="List of day plans in the Itinerary",
    )

    # Summary information
    summary: ItinerarySummary = Field(
        default_factory=ItinerarySummary, description="Itinerary summary"
    )

    # Timestamps
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Preference information (for future modifications)
    interests: list[str] = Field(default_factory=list, description="User interests")
    budget_level: BudgetLevel = Field(
        default=BudgetLevel.MODERATE, description="Budget level"
    )
    num_travelers: int = Field(default=1, description="Number of travelers")

    # Extension fields
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )
