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


# Mapping from TravelInterest to MongoDB attraction tags (景点标签)
TRAVEL_INTEREST_TO_ATTRACTION_TAGS: dict[TravelInterest, list[str]] = {
    TravelInterest.CULTURE: [
        "人文景观",
        "博物馆",
        "美术馆",
        "艺术馆",
        "文化旅游区",
        "其他",
    ],
    TravelInterest.CLASSIC: ["历史古迹", "纪念馆", "红色景点", "人文景观", "其他"],
    TravelInterest.NATURE: ["自然风光", "公园", "其他"],
    TravelInterest.CITYSCAPE: ["商业街区", "大学校园", "公园", "人文景观", "其他"],
    TravelInterest.HISTORY: ["历史古迹", "纪念馆", "红色景点", "博物馆", "其他"],
}


def get_attraction_tags_for_interests(interests: list[TravelInterest]) -> list[str]:
    """Return deduplicated attraction tags for the given travel interests."""
    if not interests:
        return [
            "人文景观",
            "体育娱乐",
            "公园",
            "其它",
            "博物馆",
            "历史古迹",
            "商业街区",
            "大学校园",
            "文化旅游区",
            "游乐园",
            "红色景点",
            "纪念馆",
            "美术馆",
            "自然风光",
            "艺术馆",
            "其他",
        ]
    tags: list[str] = []
    seen: set[str] = set()
    for interest in interests:
        for tag in TRAVEL_INTEREST_TO_ATTRACTION_TAGS.get(interest, []):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


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
    highlights: list[str] = Field(default_factory=list, description="Trip highlights")


class Itinerary(BaseModel):
    id: str = Field(description="Unique itinerary identifier")
    destination: str = Field(description="Destination name")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    day_plans: list[DayPlan] = Field(
        default_factory=list[DayPlan], description="Daily plans"
    )
    summary: ItinerarySummary | None = Field(
        default=None, description="Itinerary summary with cost and highlights"
    )
