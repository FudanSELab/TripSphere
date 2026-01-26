import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from itinerary_planner.agent.state import PlanningState
from itinerary_planner.agent.workflow import create_planning_workflow
from itinerary_planner.common.deps import provide_nacos_naming
from itinerary_planner.models.itinerary import Itinerary, TravelInterest, TripPace
from itinerary_planner.models.planning import PlanningProgressEvent
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.utils.sse import encode

logger = logging.getLogger(__name__)


_workflow = create_planning_workflow()


class PlanItineraryRequest(BaseModel):
    user_id: str = Field(description="User ID")
    destination: str = Field(description="Destination name")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    interests: list[TravelInterest] = Field(
        default_factory=list[TravelInterest],
        description="Selected travel interests",
        examples=[[TravelInterest.CULTURE, TravelInterest.CLASSIC]],
    )
    pace: TripPace = Field(default=TripPace.MODERATE, description="Trip pace")
    additional_preferences: str = Field(
        default="", description="Additional preferences"
    )


planning = APIRouter(prefix="/itineraries/plannings", tags=["Itineraries Plannings"])


def get_initial_state(
    request: PlanItineraryRequest, nacos_naming: NacosNaming
) -> PlanningState:
    return PlanningState(
        nacos_naming=nacos_naming,
        user_id=request.user_id,
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        interests=request.interests,
        pace=request.pace,
        additional_preferences=request.additional_preferences,
        # Initialize working data fields
        destination_info="",
        destination_coords={},
        activity_suggestions=[],
        attraction_details={},
        daily_schedule={},
        # Initialize output fields
        itinerary=None,
        error=None,
        events=[],
    )


@planning.post("", status_code=201)
async def plan_itinerary(
    request: PlanItineraryRequest,
    nacos_naming: Annotated[NacosNaming, Depends(provide_nacos_naming)],
) -> Itinerary:
    logger.info(f"Planning itinerary for {request.destination}")

    initial_state: PlanningState = get_initial_state(request, nacos_naming)

    try:
        # Run workflow to completion
        final_state = await _workflow.ainvoke(initial_state)  # pyright: ignore

        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])

        itinerary: Itinerary | None = final_state.get("itinerary")
        if itinerary is None:
            raise HTTPException(status_code=500, detail="Failed to generate itinerary")

        return itinerary
    except Exception as e:
        logger.exception(f"Error planning itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_events(initial_state: PlanningState) -> AsyncGenerator[str, None]:
    try:
        async for chunk in _workflow.astream(initial_state, stream_mode="updates"):  # pyright: ignore
            # Chunk is a dict with node name as key
            for _, node_state in chunk.items():
                events: list[PlanningProgressEvent] = node_state.get("events", [])
                if len(events) > 0:
                    yield encode(data=events[0].model_dump_json())

        # Send completion event after workflow finishes
        yield encode(event="completed", data="")

    except Exception as e:
        logger.exception(f"Error in planning stream: {e}")
        yield encode(event="failed", data=f"Error in planning stream: {e}")


@planning.post("/stream", status_code=201)
async def plan_itinerary_stream(
    request: PlanItineraryRequest,
    nacos_naming: Annotated[NacosNaming, Depends(provide_nacos_naming)],
) -> StreamingResponse:
    logger.info(f"Streaming itinerary planning for {request.destination}")

    initial_state: PlanningState = get_initial_state(request, nacos_naming)

    return StreamingResponse(
        _stream_events(initial_state), media_type="text/event-stream"
    )
