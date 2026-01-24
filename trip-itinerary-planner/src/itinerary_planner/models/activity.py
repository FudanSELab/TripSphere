from pydantic import BaseModel, Field


class ActivityLocation(BaseModel):
    """Location information for an activity."""

    name: str = Field(description="Location name")
    longitude: float = Field(default=0.0, description="Longitude coordinate")
    latitude: float = Field(default=0.0, description="Latitude coordinate")
    address: str = Field(default="", description="Full address")


class Cost(BaseModel):
    """Cost information."""

    amount: float = Field(description="Cost amount")
    currency: str = Field(default="CNY", description="Currency code (ISO 4217)")


class Activity(BaseModel):
    id: str = Field(description="Unique activity identifier")
    name: str = Field(description="Activity name")
    description: str = Field(description="Detailed description of the activity")
    start_time: str = Field(description="Start time in HH:MM format")
    end_time: str = Field(description="End time in HH:MM format")
    location: ActivityLocation = Field(description="Activity location")
    category: str = Field(
        description="Category: sightseeing, shopping, entertainment, "
        "cultural, transportation"
    )
    estimated_cost: Cost = Field(description="Estimated cost")
    kind: str = Field(
        default="attraction_visit",
        description="Activity kind: attraction_visit, hotel_stay, transport, custom",
    )
    attraction_id: str | None = Field(
        default=None, description="Associated attraction ID if applicable"
    )
    hotel_id: str | None = Field(
        default=None, description="Associated hotel ID if applicable"
    )


class ActivitySuggestion(BaseModel):
    """Activity suggestion with additional planning metadata."""

    name: str = Field(description="Activity name")
    description: str = Field(description="Activity description")
    category: str = Field(description="Activity category")
    estimated_duration_hours: float = Field(description="Estimated duration in hours")
    estimated_cost: float = Field(description="Estimated cost per person")
    location_name: str = Field(description="Location name or area")
    time_of_day_preference: str = Field(
        description="Preferred time: morning, afternoon, evening, any"
    )
