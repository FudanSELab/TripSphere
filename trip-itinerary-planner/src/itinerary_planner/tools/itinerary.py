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
from pydantic import BaseModel, Field

from itinerary_planner.config.settings import get_settings
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.tools.attractions import search_attractions_nearby

logger = logging.getLogger(__name__)

_FALLBACK_LONGITUDE = 121.4737
_FALLBACK_LATITUDE = 31.2304


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
    summary["total_estimated_cost"] = round(total_cost)
    return {**itinerary, "summary": summary}


def _ok(tool_call_id: str, message: str) -> Command:  # type: ignore[type-arg]
    """Return a Command that only adds a ToolMessage (no state change)."""
    return Command(
        update={"messages": [ToolMessage(content=message, tool_call_id=tool_call_id)]}
    )


def _update(
    tool_call_id: str,
    message: str,
    new_itinerary: dict[str, Any],
) -> Command:  # type: ignore[type-arg]
    """Return a Command that updates itinerary + adds a ToolMessage."""
    return Command(
        update={
            "itinerary": _recompute_summary(new_itinerary),
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

    cleaned_activities = [
        {
            **a,
            "id": a.get("id") or f"activity-{uuid.uuid4().hex[:8]}",
            "estimated_cost": {
                "amount": float((a.get("estimated_cost") or {}).get("amount", 0)),
                "currency": (a.get("estimated_cost") or {}).get("currency", "CNY"),
            },
        }
        for a in activities
    ]

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

    act = {
        **activity,
        "id": activity.get("id") or f"activity-{uuid.uuid4().hex[:8]}",
        "estimated_cost": {
            "amount": float((activity.get("estimated_cost") or {}).get("amount", 0)),
            "currency": (activity.get("estimated_cost") or {}).get("currency", "CNY"),
        },
    }
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
    return _update(tool_call_id, msg, new_itinerary)


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

    filtered = [dp for dp in day_plans if dp.get("day_number") != day]
    if not filtered:
        return _ok(tool_call_id, f"Day {day} deleted; itinerary is now empty.")

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
    new_day: dict[str, Any] = {
        "day_number": new_day_number,
        "date": date,
        "activities": [
            {
                **a,
                "id": a.get("id") or f"activity-{uuid.uuid4().hex[:8]}",
                "estimated_cost": {
                    "amount": float((a.get("estimated_cost") or {}).get("amount", 0)),
                    "currency": (a.get("estimated_cost") or {}).get("currency", "CNY"),
                },
            }
            for a in activities
        ],
        "notes": clean_notes,
    }
    new_itinerary = {
        **itinerary,
        "day_plans": [*day_plans, new_day],
        "end_date": date,
    }
    return _update(tool_call_id, f"Day {new_day_number} ({date}) added.", new_itinerary)


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
        name: str = Field(description="Activity / attraction name")
        description: str = Field(description="Short description (≤ 40 chars)")
        category: str = Field(
            description="sightseeing|cultural|shopping|dining|entertainment|transportation|nature"
        )
        start_time: str = Field(description="HH:MM")
        end_time: str = Field(description="HH:MM")
        estimated_cost: float = Field(description="Estimated cost in CNY")
        longitude: float = Field(description="Actual longitude of the location")
        latitude: float = Field(description="Actual latitude of the location")
        address: str = Field(description="Full address")

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

        # Pick destination coords from first activity with valid coordinates
        dest_lon = _FALLBACK_LONGITUDE
        dest_lat = _FALLBACK_LATITUDE
        for dp in day_plans:
            for act in dp.get("activities", []):
                loc = act.get("location") or {}
                if loc.get("longitude") and loc.get("latitude"):
                    dest_lon = float(loc["longitude"])
                    dest_lat = float(loc["latitude"])
                    break
            else:
                continue
            break

        # Search for fresh attractions
        try:
            search_result = await search_attractions_nearby(
                nacos_naming=nacos_naming,
                center_longitude=dest_lon,
                center_latitude=dest_lat,
                radius_km=25.0,
                limit=20,
            )
            attractions_text = "\n".join(
                (
                    f"- {a.name}: {a.description} "
                    f"(lat={a.latitude:.4f}, lon={a.longitude:.4f}, tags={a.tags})"
                )
                for a in search_result.attractions
            )
            attraction_map = {a.name: a for a in search_result.attractions}
        except Exception as exc:
            logger.warning("Attraction search failed for regenerate_day: %s", exc)
            attractions_text = f"General attractions in {destination}"
            attraction_map = {}

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
            f"When available, use the EXACT name and coordinates from the list above. "
            f"Keep all activities within {destination}."
        )

        try:
            structured_llm = chat_model.with_structured_output(_RegResult)
            result: _RegResult = _RegResult.model_validate(
                await structured_llm.ainvoke(prompt)
            )

            new_activities: list[dict[str, Any]] = []
            for act in result.activities:
                # Try to enrich with exact coordinates from attraction service
                matched = attraction_map.get(act.name)
                lon = matched.longitude if matched else act.longitude
                lat = matched.latitude if matched else act.latitude
                addr = matched.address if matched else act.address
                attraction_id = matched.id if matched else None
                new_activities.append(
                    {
                        "id": f"activity-{uuid.uuid4().hex[:8]}",
                        "name": act.name,
                        "description": act.description,
                        "start_time": act.start_time,
                        "end_time": act.end_time,
                        "category": act.category,
                        "location": {
                            "name": act.name,
                            "longitude": lon,
                            "latitude": lat,
                            "address": addr,
                        },
                        "estimated_cost": {
                            "amount": act.estimated_cost,
                            "currency": "CNY",
                        },
                        "kind": "attraction_visit",
                        "attraction_id": attraction_id,
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
            new_itinerary,
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
