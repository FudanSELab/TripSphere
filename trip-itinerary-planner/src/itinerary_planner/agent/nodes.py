import logging
import random
import uuid
from datetime import date, timedelta
from typing import Any

from langchain_openai import ChatOpenAI

from itinerary_planner.agent.exceptions import (
    InvalidPlanningResultError,
    PlanningDependencyError,
)
from itinerary_planner.agent.state import PlanningState
from itinerary_planner.agent.validation import (
    coordinates_are_valid,
    validate_generated_plan,
    validate_itinerary,
)
from itinerary_planner.config.settings import get_settings
from itinerary_planner.models.activity import Activity, ActivityLocation, Cost
from itinerary_planner.models.itinerary import (
    DayPlan,
    Itinerary,
    ItinerarySummary,
    get_attraction_tags_for_interests,
)
from itinerary_planner.models.planning import (
    GeneratedItineraryPlan,
    PlanningProgressEvent,
    PlanningStep,
)
from itinerary_planner.prompts.workflow import (
    MARKDOWN_GENERATION_PROMPT,
    RESEARCH_AND_PLAN_PROMPT,
)
from itinerary_planner.tools import (
    AttractionDetail,
    GeocodeResult,
    geocoding_tool,
    search_attractions_nearby,
    search_hotels_nearby,
)

logger = logging.getLogger(__name__)

_ATTRACTION_SAMPLE_SIZE = 15

chat_model = ChatOpenAI(
    model="gpt-5.5",
    temperature=0.0,
    api_key=get_settings().openai.api_key,
    base_url=get_settings().openai.base_url,
)


async def _geocode_destination(destination: str) -> dict[str, Any]:
    try:
        geocode_result: GeocodeResult = await geocoding_tool.ainvoke(
            {"address": destination, "city": destination}
        )
    except Exception as exc:
        raise PlanningDependencyError(
            f"Unable to resolve coordinates for destination '{destination}'"
        ) from exc

    if not coordinates_are_valid(
        geocode_result.longitude,
        geocode_result.latitude,
    ):
        raise PlanningDependencyError(
            f"Geocoding returned invalid coordinates for destination '{destination}'"
        )

    logger.info("Geocoded %s to valid coordinates", destination)
    return {
        "longitude": geocode_result.longitude,
        "latitude": geocode_result.latitude,
        "address": geocode_result.address or destination,
    }


async def _find_attraction_candidates(
    state: PlanningState,
    destination_coords: dict[str, Any],
) -> list[AttractionDetail]:
    tags = get_attraction_tags_for_interests(state.get("interests", []))
    try:
        search_result = await search_attractions_nearby(
            nacos_naming=state["nacos_naming"],
            center_longitude=float(destination_coords.get("longitude") or 0),  # type: ignore[arg-type]
            center_latitude=float(destination_coords.get("latitude") or 0),  # type: ignore[arg-type]
            radius_km=25.0,
            tags=tags,
            limit=35,
        )
    except Exception as exc:
        raise PlanningDependencyError(
            "Unable to load attraction candidates for itinerary planning"
        ) from exc

    valid_attractions = [
        attraction
        for attraction in search_result.attractions
        if attraction.id.strip()
        and attraction.name.strip()
        and coordinates_are_valid(attraction.longitude, attraction.latitude)
    ]
    if not valid_attractions:
        raise PlanningDependencyError(
            "Attraction service returned no usable candidates for the destination"
        )

    sample_size = min(_ATTRACTION_SAMPLE_SIZE, len(valid_attractions))
    selected = random.sample(valid_attractions, sample_size)
    logger.info(
        "Selected %d of %d valid attraction candidates",
        len(selected),
        len(valid_attractions),
    )
    return selected


async def _generate_itinerary_plan(
    state: PlanningState,
    attractions: list[AttractionDetail],
    num_days: int,
) -> GeneratedItineraryPlan:
    attractions_text = "\n".join(
        f"- {attraction.name}: {attraction.description} "
        f"(Tags: {', '.join(attraction.tags)})"
        for attraction in attractions
    )

    interests_str = ", ".join(state.get("interests", [])) or "general travel"
    pace = state.get("pace", "moderate")
    pace_activities = {"relaxed": 2, "moderate": 3, "intense": 4}
    activities_per_day = pace_activities.get(pace, 3)
    structured_llm = chat_model.with_structured_output(GeneratedItineraryPlan)  # pyright: ignore

    prompt = RESEARCH_AND_PLAN_PROMPT.format(
        num_days=num_days,
        destination=state["destination"],
        interests=interests_str,
        pace=pace,
        activities_per_day=activities_per_day,
        start_date=state["start_date"],
        end_date=state["end_date"],
        additional_preferences=state.get("additional_preferences", ""),
        attractions=attractions_text,
    )

    try:
        itinerary_plan = await structured_llm.ainvoke(prompt)  # pyright: ignore
        validated_plan = GeneratedItineraryPlan.model_validate(itinerary_plan)
        validate_generated_plan(validated_plan, num_days)
        return validated_plan
    except InvalidPlanningResultError:
        raise
    except Exception as exc:
        raise PlanningDependencyError(
            "The itinerary model returned an invalid planning result"
        ) from exc


async def _find_hotel_candidates(
    state: PlanningState,
    itinerary_plan: GeneratedItineraryPlan,
    attraction_details: dict[str, dict[str, Any]],
    destination_coords: dict[str, Any],
    num_days: int,
) -> list[dict[str, Any]]:
    matched_attractions = [
        match
        for day_plan in itinerary_plan.day_plans
        for activity in day_plan.activities
        if (match := _find_matching_attraction(activity.name, attraction_details))
    ]
    if matched_attractions:
        center_lat = sum(item["latitude"] for item in matched_attractions) / len(
            matched_attractions
        )
        center_lon = sum(item["longitude"] for item in matched_attractions) / len(
            matched_attractions
        )
    else:
        center_lat = destination_coords["latitude"]
        center_lon = destination_coords["longitude"]

    try:
        hotel_result = await search_hotels_nearby(
            nacos_naming=state["nacos_naming"],
            center_longitude=center_lon,
            center_latitude=center_lat,
            radius_km=12.0,
            limit=3 if num_days <= 4 else 5,
        )
    except Exception as exc:
        raise PlanningDependencyError(
            "Unable to load hotel candidates for itinerary planning"
        ) from exc

    valid_hotels = [
        hotel.model_dump()
        for hotel in hotel_result.hotels
        if hotel.id.strip()
        and hotel.name.strip()
        and coordinates_are_valid(hotel.longitude, hotel.latitude)
    ]
    logger.info(
        "Found %d valid hotels near attractions center (%.4f, %.4f)",
        len(valid_hotels),
        center_lat,
        center_lon,
    )
    return valid_hotels


async def research_and_plan(state: PlanningState) -> dict[str, Any]:
    """Research the destination and build a validated planning schedule."""
    destination = state["destination"]
    logger.info("Researching destination and planning activities for %s", destination)

    start = date.fromisoformat(state["start_date"])
    end = date.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    destination_coords = await _geocode_destination(destination)
    attractions = await _find_attraction_candidates(state, destination_coords)
    itinerary_plan = await _generate_itinerary_plan(state, attractions, num_days)
    attraction_details = {
        attraction.name: attraction.model_dump() for attraction in attractions
    }

    daily_schedule: dict[int, list[dict[str, Any]]] = {}
    for day_plan in itinerary_plan.day_plans:
        daily_schedule[day_plan.day_number] = []
        for activity in day_plan.activities:
            attraction = _find_matching_attraction(
                activity.name,
                attraction_details,
            )
            daily_schedule[day_plan.day_number].append(
                {
                    "name": activity.name,
                    "start_time": activity.start_time,
                    "end_time": activity.end_time,
                    "description": activity.description,
                    "category": activity.category,
                    "location": activity.name,
                    "estimated_cost": activity.estimated_cost,
                    "attraction_id": attraction.get("id") if attraction else None,
                }
            )

    hotel_details = await _find_hotel_candidates(
        state,
        itinerary_plan,
        attraction_details,
        destination_coords,
        num_days,
    )

    # Create progress event
    progress_event = PlanningProgressEvent(
        progress_percentage=70,
        status_message=f"Planning {num_days}-day trip to {state['destination']}...",
        current_step=PlanningStep.RESEARCHING_DESTINATION,
        itinerary=None,
    )

    return {
        "destination_info": itinerary_plan.destination_info,
        "destination_coords": destination_coords,
        "attraction_details": attraction_details,
        "daily_schedule": daily_schedule,
        "hotel_details": hotel_details,
        "progress_percentage": 70,
        "events": [progress_event],
    }


def _find_matching_attraction(
    location_name: str, attraction_details: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Find an attraction without guessing across different entity names."""
    if location_name in attraction_details:
        return attraction_details[location_name]

    location_lower = location_name.lower()
    for name, details in attraction_details.items():
        if name.lower() == location_lower:
            return details

    return None


async def finalize_itinerary(state: PlanningState) -> dict[str, Any]:
    """Step 2: Finalize the itinerary with proper data structures."""
    logger.info("Finalizing itinerary with proper data structures")

    start = date.fromisoformat(state["start_date"])
    end = date.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    attraction_details = state.get("attraction_details", {})
    daily_schedule = state.get("daily_schedule", {})
    hotel_details: list[dict[str, Any]] = state.get("hotel_details", [])

    # Assign which hotel for each night:
    # short trip 1 hotel, longer trip can use multiple
    def _hotel_for_night(night_index: int) -> dict[str, Any] | None:
        if not hotel_details:
            return None
        if len(hotel_details) == 1:
            return hotel_details[0]
        # Spread multiple hotels over nights
        # (e.g. 6 days -> hotel0 for nights 0,1,2 and hotel1 for 3,4,5)
        nights_per_hotel = max(
            1, (num_days + len(hotel_details) - 1) // len(hotel_details)
        )
        hotel_idx = min(night_index // nights_per_hotel, len(hotel_details) - 1)
        return hotel_details[hotel_idx]

    # Build day plans with coordinates
    day_plans: list[DayPlan] = []
    total_cost = 0.0
    total_activities = 0

    for day_num in range(1, num_days + 1):
        day_date = (start + timedelta(days=day_num - 1)).isoformat()
        daily_activities = daily_schedule.get(day_num, [])

        formatted_activities: list[Activity] = []
        for activity_data in daily_activities:
            activity_name = activity_data.get("name", "Activity")
            location_name = activity_data.get("location", activity_name)

            attraction_info = _find_matching_attraction(
                location_name, attraction_details
            )

            if attraction_info:
                location = ActivityLocation(
                    name=location_name,
                    longitude=attraction_info["longitude"],
                    latitude=attraction_info["latitude"],
                    address=attraction_info["address"],
                )
                attraction_id = attraction_info["id"]
                activity_kind = "attraction_visit"
            else:
                logger.info(
                    "No matching attraction for '%s'; treating it as a custom "
                    "activity at the validated destination coordinates",
                    location_name,
                )
                dest_coords = state.get("destination_coords", {})
                location = ActivityLocation(
                    name=location_name,
                    latitude=dest_coords["latitude"],
                    longitude=dest_coords["longitude"],
                    address=dest_coords.get("address", location_name),
                )
                attraction_id = None
                activity_kind = "custom"

            # Calculate cost
            activity_cost = activity_data.get("estimated_cost", 0)
            total_cost += activity_cost
            total_activities += 1

            # Create activity with unique ID
            activity = Activity(
                id=str(uuid.uuid4()),
                name=activity_name,
                description=activity_data.get("description", ""),
                start_time=activity_data.get("start_time", "09:00"),
                end_time=activity_data.get("end_time", "11:00"),
                location=location,
                category=activity_data.get("category", "sightseeing"),
                estimated_cost=Cost(amount=activity_cost, currency="CNY"),
                kind=activity_kind,
                attraction_id=attraction_id,
            )
            formatted_activities.append(activity)

        # Append accommodation for this night (hotel near attractions center)
        hotel_for_night = _hotel_for_night(day_num - 1)
        if hotel_for_night:
            hotel_name = hotel_for_night.get("name", "酒店")
            stay_label = (
                "入住: " + hotel_name if day_num == 1 else "当晚住宿: " + hotel_name
            )
            price_per_night = hotel_for_night.get("estimated_price") or 0.0
            formatted_activities.append(
                Activity(
                    id=str(uuid.uuid4()),
                    name=stay_label,
                    description=hotel_for_night.get("introduction", "")
                    or hotel_for_night.get("address", ""),
                    start_time="20:00",
                    end_time="08:00",
                    location=ActivityLocation(
                        name=hotel_name,
                        latitude=hotel_for_night.get("latitude", 0.0),
                        longitude=hotel_for_night.get("longitude", 0.0),
                        address=hotel_for_night.get("address", ""),
                    ),
                    category="accommodation",
                    estimated_cost=Cost(amount=price_per_night, currency="CNY"),
                    kind="hotel_stay",
                    hotel_id=hotel_for_night.get("id"),
                )
            )
            total_cost += price_per_night
            total_activities += 1

        day_plan = DayPlan(
            day_number=day_num,
            date=day_date,
            activities=formatted_activities,
            notes=f"Day {day_num} in {state['destination']}",
        )
        day_plans.append(day_plan)

    # Generate basic highlights
    highlights = [
        f"Explore the best of {state['destination']}",
        "Experience local culture and cuisine",
        "Visit iconic landmarks and attractions",
    ]

    # Create itinerary summary
    summary = ItinerarySummary(
        total_estimated_cost=round(total_cost, 2),
        currency="CNY",
        total_activities=total_activities,
        highlights=highlights,
    )

    # Create final itinerary
    itinerary = Itinerary(
        id=str(uuid.uuid4()),
        destination=state["destination"],
        start_date=state["start_date"],
        end_date=state["end_date"],
        day_plans=day_plans,
        summary=summary,
    )
    validate_itinerary(
        itinerary,
        valid_attraction_ids={
            details["id"] for details in attraction_details.values()
        },
        valid_hotel_ids={hotel["id"] for hotel in hotel_details},
    )

    # Create progress event — 85% because markdown + conversation context follow
    progress_event = PlanningProgressEvent(
        progress_percentage=85,
        status_message=f"Itinerary structure ready for {state['destination']}…",
        current_step=PlanningStep.FINALIZING,
        itinerary=itinerary,
    )

    logger.info(
        f"Itinerary finalized: {len(day_plans)} days, {total_activities} activities"
    )

    return {
        "itinerary": itinerary,
        "progress_percentage": 100,
        "events": [progress_event],
        "error": None,
    }


async def generate_markdown(state: PlanningState) -> dict[str, Any]:
    """Step 3: Generate natural-language Markdown from the structured itinerary."""
    logger.info("Generating Markdown itinerary content")

    itinerary = state.get("itinerary")
    if itinerary is None:
        return {"markdown_content": "", "events": []}

    itinerary_json = itinerary.model_dump_json(indent=2)

    prompt = MARKDOWN_GENERATION_PROMPT.format(itinerary_json=itinerary_json)

    try:
        result = await chat_model.ainvoke(prompt)
        markdown_content = str(result.content)
    except Exception as e:
        logger.error(f"Markdown generation failed: {e}")
        markdown_content = _build_fallback_markdown(itinerary)

    progress_event = PlanningProgressEvent(
        progress_percentage=95,
        status_message="生成行程文案中……",
        current_step=PlanningStep.OPTIMIZING_ROUTE,
        itinerary=None,
    )

    return {"markdown_content": markdown_content, "events": [progress_event]}


def _build_fallback_markdown(itinerary: Itinerary) -> str:
    """Build a simple Markdown fallback when LLM generation fails."""
    lines: list[str] = [
        f"# {itinerary.destination} 旅行计划",
        f"\n**日期**: {itinerary.start_date} ~ {itinerary.end_date}\n",
    ]
    for day in itinerary.day_plans:
        lines.append(f"## 第{day.day_number}天 ({day.date})\n")
        for act in day.activities:
            lines.append(
                f"- **{act.start_time}-{act.end_time}** {act.name}  "
                f"\n  {act.description}"
            )
        lines.append("")
    return "\n".join(lines)
