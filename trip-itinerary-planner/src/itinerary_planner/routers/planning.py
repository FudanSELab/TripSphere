import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from itinerary_planner.models.itinerary import Itinerary, TravelInterest, TripPace

logger = logging.getLogger(__name__)


class PlanItineraryRequest(BaseModel):
    user_id: str = Field(description="User ID")
    destination: str = Field(description="Destination name")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    interests: list[TravelInterest] = Field(
        default_factory=list,
        description="Selected travel interests",
        examples=[[TravelInterest.CULTURE, TravelInterest.CLASSIC]],
    )
    pace: TripPace = Field(default=TripPace.MODERATE, description="Trip pace")
    additional_preferences: str = Field(
        default="", description="Additional preferences"
    )


planning = APIRouter(prefix="/itineraries/plannings", tags=["Itineraries Plannings"])


@planning.post("")
async def plan_itinerary(request: PlanItineraryRequest) -> Itinerary:
    raise NotImplementedError


@planning.post(":stream")
async def plan_itinerary_stream(request: PlanItineraryRequest) -> StreamingResponse:
    raise NotImplementedError
