"""Backend tools for itinerary modification used by the ReAct chat agent.

Each tool uses InjectedState to read the current itinerary from the graph
state and returns a Command that atomically updates `itinerary` (and/or
`markdown_content`) together with a properly-formed ToolMessage so the LLM
receives a useful acknowledgement.

The itinerary is stored as a plain `dict[str, Any]` (the JSON-serializable
form) so it survives checkpointing and AG-UI state-snapshot events without
custom serialisation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from pydantic import BaseModel, Field, ValidationError

from itinerary_planner.agent.exceptions import InvalidPlanningResultError
from itinerary_planner.agent.validation import (
    coordinates_are_valid,
    validate_itinerary,
)
from itinerary_planner.config.settings import get_settings
from itinerary_planner.models.itinerary import Itinerary
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.tools.attractions import search_attractions_nearby
from itinerary_planner.tools.geocoding import GeocodeResult, geocoding_tool

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────


def _add_days(date_str: str, days: int) -> str:
    """Add *days* to a YYYY-MM-DD string; returns YYYY-MM-DD."""
    d = datetime.fromisoformat(date_str) + timedelta(days=days)
    return d.strftime("%Y-%m-%d")


def _recompute_summary(itinerary: dict[str, Any]) -> dict[str, Any]:
    """Recompute summary totals from the current day_plans."""
    day_plans: list[dict[str, Any]] = itinerary.get("day_plans") or []
    all_activities = [a for dp in day_plans for a in dp.get("activities", [])]
    total_cost = sum(
        float(a.get("estimated_cost", {}).get("amount", 0)) for a in all_activities
    )
    summary: dict[str, Any] = dict(itinerary.get("summary") or {})
    summary["total_activities"] = len(all_activities)
    summary["total_estimated_cost"] = round(total_cost, 2)
    return {**itinerary, "summary": summary}


def _normalize_activity(activity: dict[str, Any]) -> dict[str, Any]:
    estimated_cost = activity.get("estimated_cost") or {}
    return {
        **activity,
        "id": activity.get("id") or f"activity-{uuid.uuid4().hex[:8]}",
        "estimated_cost": {
            "amount": float(estimated_cost.get("amount", 0)),
            "currency": estimated_cost.get("currency", "CNY"),
        },
    }


def _ok(tool_call_id: str, message: str) -> Command:  # type: ignore[type-arg]
    """Return a Command that only adds a ToolMessage (no state change)."""
    return Command(
        update={"messages": [ToolMessage(content=message, tool_call_id=tool_call_id)]}
    )


def _trusted_entity_coordinates(
    itinerary: dict[str, Any],
) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float]]]:
    attractions: dict[str, tuple[float, float]] = {}
    hotels: dict[str, tuple[float, float]] = {}
    for day_plan in itinerary.get("day_plans") or []:
        for activity in day_plan.get("activities") or []:
            location = activity.get("location") or {}
            try:
                coordinates = (
                    float(location.get("longitude")),
                    float(location.get("latitude")),
                )
            except (TypeError, ValueError):
                continue
            attraction_id = activity.get("attraction_id")
            hotel_id = activity.get("hotel_id")
            if isinstance(attraction_id, str) and attraction_id:
                attractions[attraction_id] = coordinates
            if isinstance(hotel_id, str) and hotel_id:
                hotels[hotel_id] = coordinates
    return attractions, hotels


def _entity_coordinates_match(
    itinerary: Itinerary,
    trusted_attractions: dict[str, tuple[float, float]],
    trusted_hotels: dict[str, tuple[float, float]],
) -> bool:
    for day_plan in itinerary.day_plans:
        for activity in day_plan.activities:
            entity_id = activity.attraction_id or activity.hotel_id
            if not entity_id:
                continue
            trusted = (
                trusted_attractions.get(entity_id)
                if activity.attraction_id
                else trusted_hotels.get(entity_id)
            )
            actual = (activity.location.longitude, activity.location.latitude)
            if trusted != actual:
                return False
    return True


def _update(
    tool_call_id: str,
    message: str,
    current_itinerary: dict[str, Any],
    new_itinerary: dict[str, Any],
    verified_attractions: dict[str, tuple[float, float]] | None = None,
) -> Command:  # type: ignore[type-arg]
    """Validate and return an itinerary state update."""
    if not new_itinerary.get("id"):
        logger.warning("Skipping itinerary update because itinerary.id is missing.")
        return _ok(tool_call_id, "No itinerary id found; skipping update.")

    trusted_attractions, trusted_hotels = _trusted_entity_coordinates(
        current_itinerary
    )
    trusted_attractions.update(verified_attractions or {})
    try:
        recomputed_itinerary = _recompute_summary(new_itinerary)
        validated_itinerary = Itinerary.model_validate(recomputed_itinerary)
        validate_itinerary(
            validated_itinerary,
            valid_attraction_ids=set(trusted_attractions),
            valid_hotel_ids=set(trusted_hotels),
        )
        if not _entity_coordinates_match(
            validated_itinerary,
            trusted_attractions,
            trusted_hotels,
        ):
            raise InvalidPlanningResultError(
                "Referenced entity coordinates do not match trusted service data"
            )
    except (InvalidPlanningResultError, ValidationError, TypeError, ValueError) as exc:
        logger.warning("Rejected invalid itinerary edit: %s", exc)
        return _ok(
            tool_call_id,
            "The requested change was not applied because it would make the "
            "itinerary invalid.",
        )

    return Command(
        update={
            "itinerary": validated_itinerary.model_dump(mode="json"),
            "messages": [ToolMessage(content=message, tool_call_id=tool_call_id)],
        }
    )


# ── Inline tools ───────────────────────────────────────────────────────────


@tool
def update_itinerary_day(
    day: int,
    activities: list[dict[str, Any]],
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:  # type: ignore[type-arg]
    """Replace ALL activities for a specific day with a new list.

    Arguments:
        day: The day number to update (1-indexed)
        activities: List of activities to replace the existing activities for the day
        tool_call_id: The ID of the tool call
        state: The state of the itinerary

    Returns:
    Command that updates the itinerary with the new activities

    Use this ONLY when regenerating an entire day's schedule.
    Do NOT use this to add a single activity — use add_activity instead.
    Only the specified day is modified; all other days remain unchanged.
    """
    itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
    day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])
    if not any(dp.get("day_number") == day for dp in day_plans):
        return _ok(tool_call_id, f"Day {day} not found in itinerary.")

    try:
        cleaned_activities = [_normalize_activity(activity) for activity in activities]
    except (AttributeError, TypeError, ValueError):
        return _ok(tool_call_id, "Day activities contain invalid data.")

    updated_plans = [
        (
            {**dp, "activities": cleaned_activities}
            if dp.get("day_number") == day
            else dp
        )
        for dp in day_plans
    ]
    new_itinerary = {**itinerary, "day_plans": updated_plans}
    return _update(
        tool_call_id,
        f"Day {day} activities replaced ({len(cleaned_activities)} activities).",
        itinerary,
        new_itinerary,
    )


@tool
def add_activity(
    day: int,
    activity: dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:  # type: ignore[type-arg]
    """Add a SINGLE new activity to a specific day without replacing existing ones.

    Arguments:
        day: The day number to add the activity to (1-indexed)
        activity: The activity to add to the day
        tool_call_id: The ID of the tool call
        state: The state of the itinerary

    Returns:
    Command that updates the itinerary with the new activity

    Use this whenever the user asks to add or insert one activity.
    The activity object must strictly follow the Activity schema.
    Only the specified day is affected.
    """
    itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
    day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])
    if not any(dp.get("day_number") == day for dp in day_plans):
        return _ok(tool_call_id, f"Day {day} not found in itinerary.")

    try:
        act = _normalize_activity(activity)
    except (AttributeError, TypeError, ValueError):
        return _ok(tool_call_id, "The activity contains invalid data.")
    updated_plans = [
        (
            {**dp, "activities": [*dp.get("activities", []), act]}
            if dp.get("day_number") == day
            else dp
        )
        for dp in day_plans
    ]
    new_itinerary = {**itinerary, "day_plans": updated_plans}
    return _update(
        tool_call_id,
        f'Added "{act.get("name", "activity")}" to day {day}.',
        itinerary,
        new_itinerary,
    )


@tool
def remove_spot(
    day: int,
    spot_name: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:  # type: ignore[type-arg]
    """Remove a single spot/activity from a specific day by name.

    Arguments:
        day: The day number to remove the activity from (1-indexed)
        spot_name: The name of the activity to remove
        tool_call_id: The ID of the tool call
        state: The state of the itinerary

    Returns:
    Command that updates the itinerary with the removed activity

    Only that one activity is removed; all other activities and all other
    days remain unchanged.
    """
    itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
    day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])
    spot_lower = spot_name.lower()
    removed = False

    def _filter(dp: dict[str, Any]) -> dict[str, Any]:
        nonlocal removed
        if dp.get("day_number") != day:
            return dp
        original = dp.get("activities", [])
        kept = [
            a
            for a in original
            if not (
                a.get("name", "").lower() == spot_lower
                or spot_lower in a.get("name", "").lower()
                or a.get("name", "").lower() in spot_lower
            )
        ]
        if len(kept) < len(original):
            removed = True
        return {**dp, "activities": kept}

    updated_plans = [_filter(dp) for dp in day_plans]
    new_itinerary = {**itinerary, "day_plans": updated_plans}
    msg = (
        f'Removed "{spot_name}" from day {day}.'
        if removed
        else f'"{spot_name}" not found in day {day}; no change.'
    )
    return _update(tool_call_id, msg, itinerary, new_itinerary)


@tool
def delete_day(
    day: int,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:  # type: ignore[type-arg]
    """Completely remove a day from the itinerary.

    Arguments:
        day: The day number to delete (1-indexed)
        tool_call_id: The ID of the tool call
        state: The state of the itinerary

    Returns:
    Command that updates the itinerary with the deleted day

    All activities for that day are deleted.  Remaining days are
    renumbered (1, 2, 3 …) and their dates are shifted forward to remain
    consecutive (e.g. deleting day 2 moves former day 3 to day 2's date).
    """
    itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
    day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])

    if not any(dp.get("day_number") == day for dp in day_plans):
        return _ok(tool_call_id, f"Day {day} not found in itinerary.")

    filtered = [dp for dp in day_plans if dp.get("day_number") != day]
    if not filtered:
        return _ok(tool_call_id, "An itinerary must contain at least one day.")

    first_date: str = filtered[0]["date"]
    renumbered = [
        {**dp, "day_number": i + 1, "date": _add_days(first_date, i)}
        for i, dp in enumerate(filtered)
    ]
    new_itinerary = {
        **itinerary,
        "day_plans": renumbered,
        "start_date": renumbered[0]["date"],
        "end_date": renumbered[-1]["date"],
    }
    return _update(
        tool_call_id,
        (
            f"Day {day} deleted; {len(renumbered)} remaining day(s) "
            "renumbered with consecutive dates."
        ),
        itinerary,
        new_itinerary,
    )


@tool
def add_day(
    date: str,
    activities: list[dict[str, Any]],
    notes: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict[str, Any], InjectedState],
) -> Command:  # type: ignore[type-arg]
    """Add a brand-new day to the itinerary, appended after the last existing day.

    Arguments:
        date: The date of the new day (YYYY-MM-DD)
        activities: List of activities to add to the new day
        notes: Notes for the new day
        tool_call_id: The ID of the tool call
        state: The state of the itinerary

    Returns:
    Command that updates the itinerary with the new day

    Use when the user asks to add another day, extend the trip, or add a
    Nth day that does not yet exist. All activities must be in the same
    destination city as the rest of the itinerary.
    """
    itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
    day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])

    new_day_number = len(day_plans) + 1
    clean_notes = notes if notes not in ("", "undefined", "null", None) else ""
    try:
        normalized_activities = [
            _normalize_activity(activity) for activity in activities
        ]
    except (AttributeError, TypeError, ValueError):
        return _ok(tool_call_id, "Day activities contain invalid data.")

    new_day: dict[str, Any] = {
        "day_number": new_day_number,
        "date": date,
        "activities": normalized_activities,
        "notes": clean_notes,
    }
    new_itinerary = {
        **itinerary,
        "day_plans": [*day_plans, new_day],
        "end_date": date,
    }
    return _update(
        tool_call_id,
        f"Day {new_day_number} ({date}) added.",
        itinerary,
        new_itinerary,
    )


@tool
def update_markdown(
    markdown: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:  # type: ignore[type-arg]
    """Update the Markdown travel narrative displayed in the itinerary viewer.

    Arguments:
        markdown: The Markdown content to update
        tool_call_id: The ID of the tool call

    Returns:
    Command that updates the itinerary with the new Markdown content

    Call this after significant itinerary changes to keep the narrative in
    sync with the structured data.
    """
    return Command(
        update={
            "markdown_content": markdown,
            "messages": [
                ToolMessage(
                    content="Markdown narrative updated.", tool_call_id=tool_call_id
                )
            ],
        }
    )


# ── Async factory tool (needs Nacos for attraction lookup) ─────────────────


def make_regenerate_day_tool(nacos_naming: NacosNaming) -> Any:
    """Return an async 'regenerate_day' tool that
    uses Nacos to find fresh attractions.
    """

    class _RegActivity(BaseModel):
        attraction_id: str = Field(description="Exact attraction ID from the list")
        description: str = Field(description="Short description (≤ 40 chars)")
        category: str = Field(
            description="sightseeing|cultural|shopping|dining|entertainment|transportation|nature"
        )
        start_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM")
        end_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM")
        estimated_cost: float = Field(ge=0, description="Estimated cost in CNY")

    class _RegResult(BaseModel):
        activities: list[_RegActivity] = Field(
            description="Regenerated activities for the day"
        )

    @tool("regenerate_day")
    async def regenerate_day(
        day: int,
        preference: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[dict[str, Any], InjectedState],
    ) -> Command:  # type: ignore[type-arg]
        """Completely regenerate all activities for
        a specific day using real attractions.

        Arguments:
            day: The day number to regenerate (1-indexed)
            preference: The preference/style of the itinerary
            tool_call_id: The ID of the tool call
            state: The state of the itinerary

        Returns:
        Command that updates the itinerary with the regenerated day

        Queries the attraction service for the destination, then uses the LLM
        to create a fresh schedule tailored to the given preference/style.
        Only the specified day is replaced; all other days are unchanged.
        """
        itinerary: dict[str, Any] = dict(state.get("itinerary") or {})
        day_plans: list[dict[str, Any]] = list(itinerary.get("day_plans") or [])
        target = next((dp for dp in day_plans if dp.get("day_number") == day), None)
        if target is None:
            return _ok(tool_call_id, f"Day {day} not found in itinerary.")

        destination: str = itinerary.get("destination", "")

        destination_coordinates: tuple[float, float] | None = None
        for dp in day_plans:
            for act in dp.get("activities", []):
                loc = act.get("location") or {}
                try:
                    longitude = float(loc.get("longitude") or 0)
                    latitude = float(loc.get("latitude") or 0)
                except (TypeError, ValueError):
                    continue
                if coordinates_are_valid(longitude, latitude):
                    destination_coordinates = (longitude, latitude)
                    break
            if destination_coordinates:
                break

        if destination_coordinates is None:
            try:
                geocode_result: GeocodeResult = await geocoding_tool.ainvoke(
                    {"address": destination, "city": destination}
                )
            except Exception as exc:
                logger.warning(
                    "Geocoding failed for regenerate_day in %s: %s",
                    destination,
                    exc,
                )
                return _ok(
                    tool_call_id,
                    f"Cannot regenerate day {day}: destination coordinates are unavailable.",
                )

            if not coordinates_are_valid(
                geocode_result.longitude,
                geocode_result.latitude,
            ):
                return _ok(
                    tool_call_id,
                    f"Cannot regenerate day {day}: geocoding returned invalid coordinates.",
                )
            destination_coordinates = (
                geocode_result.longitude,
                geocode_result.latitude,
            )

        dest_lon, dest_lat = destination_coordinates

        # Search for fresh attractions
        try:
            search_result = await search_attractions_nearby(
                nacos_naming=nacos_naming,
                center_longitude=dest_lon,
                center_latitude=dest_lat,
                radius_km=25.0,
                limit=20,
            )
            valid_attractions = [
                attraction
                for attraction in search_result.attractions
                if attraction.id.strip()
                and attraction.name.strip()
                and coordinates_are_valid(
                    attraction.longitude,
                    attraction.latitude,
                )
            ]
            if not valid_attractions:
                return _ok(
                    tool_call_id,
                    f"Cannot regenerate day {day}: no usable attractions were found.",
                )
            attractions_text = "\n".join(
                (
                    f"- id={a.id}; name={a.name}; description={a.description}; "
                    f"tags={a.tags}"
                )
                for a in valid_attractions
            )
            attraction_map = {a.id: a for a in valid_attractions}
        except Exception as exc:
            logger.warning("Attraction search failed for regenerate_day: %s", exc)
            return _ok(
                tool_call_id,
                f"Cannot regenerate day {day}: attraction service is unavailable.",
            )

        # Ask LLM to regenerate the day
        from langchain_openai import ChatOpenAI  # local import to avoid circular deps

        settings = get_settings()
        chat_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.6,
            api_key=settings.openai.api_key,
            base_url=settings.openai.base_url,
        )

        prompt = (
            f"Regenerate day {day} of a trip to {destination}.\n"
            f"Date: {target.get('date', '')}\n"
            f"User preference / style: {preference}\n\n"
            f"Available attractions:\n{attractions_text}\n\n"
            f"Generate 3–4 varied activities. "
            f"Every activity must use an exact attraction_id from the list above. "
            f"Keep all activities within {destination}."
        )

        try:
            structured_llm = chat_model.with_structured_output(_RegResult)
            result: _RegResult = _RegResult.model_validate(
                await structured_llm.ainvoke(prompt)
            )

            new_activities: list[dict[str, Any]] = []
            for act in result.activities:
                start_time = datetime.strptime(act.start_time, "%H:%M").time()
                end_time = datetime.strptime(act.end_time, "%H:%M").time()
                if start_time >= end_time:
                    return _ok(
                        tool_call_id,
                        f"Cannot regenerate day {day}: the model returned an invalid time range.",
                    )
                matched = attraction_map.get(act.attraction_id)
                if matched is None:
                    return _ok(
                        tool_call_id,
                        f"Cannot regenerate day {day}: the model selected an unknown attraction.",
                    )
                new_activities.append(
                    {
                        "id": f"activity-{uuid.uuid4().hex[:8]}",
                        "name": matched.name,
                        "description": act.description,
                        "start_time": act.start_time,
                        "end_time": act.end_time,
                        "category": act.category,
                        "location": {
                            "name": matched.name,
                            "longitude": matched.longitude,
                            "latitude": matched.latitude,
                            "address": matched.address,
                        },
                        "estimated_cost": {
                            "amount": act.estimated_cost,
                            "currency": "CNY",
                        },
                        "kind": "attraction_visit",
                        "attraction_id": matched.id,
                        "hotel_id": None,
                    }
                )
        except Exception as exc:
            logger.error("LLM regeneration failed: %s", exc)
            return _ok(tool_call_id, f"Failed to regenerate day {day}: {exc}")

        updated_plans = [
            (
                {**dp, "activities": new_activities}
                if dp.get("day_number") == day
                else dp
            )
            for dp in day_plans
        ]
        new_itinerary = {**itinerary, "day_plans": updated_plans}
        return _update(
            tool_call_id,
            (
                f"Day {day} regenerated with {len(new_activities)} "
                f'new activities (preference: "{preference}").'
            ),
            itinerary,
            new_itinerary,
            verified_attractions={
                attraction.id: (attraction.longitude, attraction.latitude)
                for attraction in attraction_map.values()
            },
        )

    return regenerate_day


# ── Public convenience: all tools except the factory one ──────────────────

# Tools that need no Nacos; regenerate_day is added via
# make_regenerate_day_tool(nacos_naming) when Nacos is enabled.
INLINE_TOOLS = [
    update_itinerary_day,
    add_activity,
    remove_spot,
    delete_day,
    add_day,
    update_markdown,
]
