import logging
from datetime import date
from typing import Annotated, AsyncGenerator, Self

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from itinerary_planner.agent.exceptions import (
    InvalidPlanningResultError,
    PlanningDependencyError,
)
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
    destination: str = Field(
        min_length=1,
        max_length=100,
        description="Destination name",
    )
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

    @field_validator("destination")
    @classmethod
    def normalize_destination(cls, value: str) -> str:
        destination = value.strip()
        if not destination:
            raise ValueError("destination must not be blank")
        return destination

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, value: str) -> str:
        normalized = value.strip()
        try:
            parsed_date = date.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("date must use YYYY-MM-DD format") from exc
        if parsed_date.isoformat() != normalized:
            raise ValueError("date must use YYYY-MM-DD format")
        return normalized

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if date.fromisoformat(self.end_date) < date.fromisoformat(self.start_date):
            raise ValueError("end_date must be on or after start_date")
        return self


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

        # Persist to itinerary service via gRPC. This must succeed so the
        # planner page can always edit a durable itinerary ID.
        try:
            saved = await svc.create_itinerary(
                itinerary=itinerary,
                user_id=user_id,
                markdown_content=markdown_content,
            )
        except Exception as exc:
            logger.exception("Failed to persist itinerary via gRPC")
            raise HTTPException(
                status_code=502,
                detail="Failed to persist generated itinerary",
            ) from exc

        if not saved.id:
            logger.error("Itinerary service returned empty id after create")
            raise HTTPException(
                status_code=502,
                detail="Itinerary persistence returned empty id",
            )

        # Use the server-assigned ID for all follow-up edits/saves.
        itinerary = itinerary.model_copy(update={"id": saved.id})

        return PlanItineraryResponse(
            itinerary=itinerary,
            markdown_content=markdown_content,
            conversation_messages=conversation_messages,
        )
    except HTTPException:
        raise
    except (PlanningDependencyError, InvalidPlanningResultError) as exc:
        logger.warning("Itinerary planning rejected an unusable result: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
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
