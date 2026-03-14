import logging
from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from itinerary_planner.agent.state import PlanningState
from itinerary_planner.agent.workflow import create_planning_workflow
from itinerary_planner.common.deps import (
    CurrentUserId,
    ItineraryRepoDep,
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


class ItinerarySummaryItem(BaseModel):
    """Lightweight representation returned by list endpoint."""

    id: str
    destination: str
    start_date: str
    end_date: str
    day_count: int
    created_at: datetime
    updated_at: datetime


class UpdateItineraryRequest(BaseModel):
    itinerary: dict[str, Any] = Field(description="Updated full itinerary JSON")
    markdown_content: str | None = Field(
        default=None, description="Updated markdown content (optional)"
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
    repo: ItineraryRepoDep,
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

        # Persist to MongoDB
        try:
            await repo.save(
                itinerary_id=itinerary.id,
                user_id=user_id,
                destination=itinerary.destination,
                start_date=itinerary.start_date,
                end_date=itinerary.end_date,
                itinerary=itinerary.model_dump(),
                markdown_content=markdown_content,
            )
        except Exception as exc:
            # Non-fatal: the itinerary is still returned even if save fails
            logger.error("Failed to persist itinerary %s: %s", itinerary.id, exc)

        return PlanItineraryResponse(
            itinerary=itinerary,
            markdown_content=markdown_content,
            conversation_messages=conversation_messages,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error planning itinerary: {e}")
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
        logger.exception(f"Error in planning stream: {e}")
        yield encode(event="failed", data=f"Error in planning stream: {e}")


@planning.post("/itineraries/plannings/stream", status_code=201)
async def plan_itinerary_stream(
    request: PlanItineraryRequest,
    nacos_naming: Annotated[NacosNaming, Depends(provide_nacos_naming)],
    user_id: CurrentUserId,
) -> StreamingResponse:
    logger.info("Streaming itinerary planning for %s", request.destination)

    initial_state = get_initial_state(request, nacos_naming, user_id)

    return StreamingResponse(
        _stream_events(initial_state), media_type="text/event-stream"
    )


# ── CRUD endpoints ─────────────────────────────────────────────────────────

@planning.get("/itineraries")
async def list_itineraries(
    user_id: CurrentUserId,
    repo: ItineraryRepoDep,
) -> list[ItinerarySummaryItem]:
    """Return a summary list of the authenticated user's saved itineraries."""
    docs = await repo.list_by_user(user_id=user_id)
    items: list[ItinerarySummaryItem] = []
    for doc in docs:
        # day_count is computed via aggregation projection
        day_count = doc.get("day_count", 0)
        items.append(
            ItinerarySummaryItem(
                id=str(doc["_id"]),
                destination=doc.get("destination", ""),
                start_date=doc.get("start_date", ""),
                end_date=doc.get("end_date", ""),
                day_count=day_count,
                created_at=doc.get("created_at", datetime.now(timezone.utc)),
                updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
            )
        )
    return items


@planning.get("/itineraries/{itinerary_id}")
async def get_itinerary(
    itinerary_id: str,
    user_id: CurrentUserId,
    repo: ItineraryRepoDep,
) -> PlanItineraryResponse:
    """Fetch a single saved itinerary owned by the authenticated user."""
    doc = await repo.get(itinerary_id=itinerary_id, user_id=user_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    try:
        itinerary = Itinerary.model_validate(doc["itinerary"])
    except Exception as exc:
        logger.error("Failed to parse stored itinerary %s: %s", itinerary_id, exc)
        raise HTTPException(status_code=500, detail="Corrupted itinerary data") from exc

    return PlanItineraryResponse(
        itinerary=itinerary,
        markdown_content=doc.get("markdown_content", ""),
        conversation_messages=[],
    )


@planning.put("/itineraries/{itinerary_id}", status_code=200)
async def update_itinerary(
    itinerary_id: str,
    body: UpdateItineraryRequest,
    user_id: CurrentUserId,
    repo: ItineraryRepoDep,
) -> dict[str, str]:
    """Replace the itinerary data for a user-owned document.

    Called automatically by the frontend's debounced sync whenever the AI
    agent modifies the in-memory itinerary.
    """
    found = await repo.update(
        itinerary_id=itinerary_id,
        user_id=user_id,
        itinerary=body.itinerary,
        markdown_content=body.markdown_content,
    )
    if not found:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return {"status": "updated"}


@planning.delete("/itineraries/{itinerary_id}", status_code=200)
async def delete_itinerary(
    itinerary_id: str,
    user_id: CurrentUserId,
    repo: ItineraryRepoDep,
) -> dict[str, str]:
    """Delete a user-owned itinerary."""
    deleted = await repo.delete(itinerary_id=itinerary_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return {"status": "deleted"}
