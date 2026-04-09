import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from itinerary_planner.agent.state import PlanningState
from itinerary_planner.agent.workflow import create_planning_workflow
from itinerary_planner.common.deps import (
    CurrentUserId,
    ItineraryServiceClientDep,
    provide_nacos_naming,
)
from itinerary_planner.models.itinerary import Itinerary, TravelInterest, TripPace
from itinerary_planner.models.planning import PlanningProgressEvent
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.utils.sse import encode

logger = logging.getLogger(__name__)

_workflow = create_planning_workflow()


# ── Request / Response models ──────────────────────────────────────────────


class PlanItineraryRequest(BaseModel):
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


class PlanItineraryResponse(BaseModel):
    itinerary: Itinerary = Field(description="Structured itinerary data")
    markdown_content: str = Field(description="Natural-language Markdown itinerary")
    conversation_messages: list[dict[str, str]] = Field(
        description="Initial conversation messages for Deep Agent handoff"
    )


# ── Router ─────────────────────────────────────────────────────────────────

planning = APIRouter(tags=["Itineraries Plannings"])


def get_initial_state(
    request: PlanItineraryRequest,
    nacos_naming: NacosNaming,
    user_id: str,
) -> PlanningState:
    return PlanningState(
        nacos_naming=nacos_naming,
        user_id=user_id,
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        interests=request.interests,
        pace=request.pace,
        additional_preferences=request.additional_preferences,
        destination_info="",
        destination_coords={},
        attraction_details={},
        daily_schedule={},
        hotel_details=[],
        itinerary=None,
        markdown_content="",
        conversation_messages=[],
        error=None,
        events=[],
    )


# ── Planning endpoints ─────────────────────────────────────────────────────


@planning.post("/itineraries/plannings", status_code=201)
async def plan_itinerary(
    request: PlanItineraryRequest,
    nacos_naming: Annotated[NacosNaming, Depends(provide_nacos_naming)],
    user_id: CurrentUserId,
    svc: ItineraryServiceClientDep,
) -> PlanItineraryResponse:
    logger.info("Planning itinerary for %s (user=%s)", request.destination, user_id)

    initial_state = get_initial_state(request, nacos_naming, user_id)

    try:
        final_state = await _workflow.ainvoke(initial_state)  # pyright: ignore

        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])

        itinerary: Itinerary | None = final_state.get("itinerary")
        if itinerary is None:
            raise HTTPException(status_code=500, detail="Failed to generate itinerary")

        markdown_content: str = final_state.get("markdown_content", "")
        conversation_messages: list[dict[str, str]] = final_state.get(
            "conversation_messages", []
        )

        # Persist to itinerary service via gRPC
        try:
            saved = await svc.create_itinerary(
                itinerary=itinerary,
                user_id=user_id,
                markdown_content=markdown_content,
            )
            # Use the server-assigned ID for subsequent operations
            itinerary = itinerary.model_copy(update={"id": saved.id})
        except Exception as exc:
            # Non-fatal: the itinerary is still returned even if save fails
            logger.error("Failed to persist itinerary via gRPC: %s", exc)

        return PlanItineraryResponse(
            itinerary=itinerary,
            markdown_content=markdown_content,
            conversation_messages=conversation_messages,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error planning itinerary: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_events(initial_state: PlanningState) -> AsyncGenerator[str, None]:
    try:
        async for chunk in _workflow.astream(initial_state, stream_mode="updates"):  # pyright: ignore
            for _, node_state in chunk.items():
                events: list[PlanningProgressEvent] = node_state.get("events", [])
                if len(events) > 0:
                    yield encode(data=events[0].model_dump_json())

        yield encode(event="completed", data="")

    except Exception as e:
        logger.exception("Error in planning stream: %s", e)
        yield encode(event="failed", data=f"Error in planning stream: {e}")


@planning.post("/itineraries/plannings/stream", status_code=201)
async def plan_itinerary_stream(
    request: PlanItineraryRequest,
    nacos_naming: Annotated[NacosNaming, Depends(provide_nacos_naming)],
    user_id: CurrentUserId,
) -> StreamingResponse:
    """Streaming SSE planning endpoint — does not persist; client fetches the
    full result from the non-streaming endpoint or gRPC directly."""
    logger.info("Streaming itinerary planning for %s", request.destination)

    initial_state = get_initial_state(request, nacos_naming, user_id)

    return StreamingResponse(
        _stream_events(initial_state), media_type="text/event-stream"
    )
