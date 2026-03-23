import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from itinerary_planner.agent.state import PlanningState
from itinerary_planner.config.settings import get_settings
from itinerary_planner.models.activity import Activity, ActivityLocation, Cost
from itinerary_planner.models.itinerary import (
    DayPlan,
    Itinerary,
    ItinerarySummary,
    get_attraction_tags_for_interests,
)
from itinerary_planner.models.planning import PlanningProgressEvent, PlanningStep
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

chat_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=get_settings().openai.api_key,
    base_url=get_settings().openai.base_url,
)


async def research_and_plan(state: PlanningState) -> dict[str, Any]:
    """Step 1: Research destination and plan activities."""
    logger.info(
        f"Researching destination and planning activities for {state['destination']}"
    )

    # Calculate trip details
    start = datetime.fromisoformat(state["start_date"])
    end = datetime.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    # Step 1: Geocode destination
    try:
        geocode_result: GeocodeResult = await geocoding_tool.ainvoke(
            {
                "address": state["destination"],
                "city": state["destination"],
            }
        )
        destination_coords = {
            "longitude": geocode_result.longitude,
            "latitude": geocode_result.latitude,
            "address": geocode_result.address,
        }
        logger.info(f"Geocoded {state['destination']} to coordinates")
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        destination_coords = {
            "longitude": 121.4737,
            "latitude": 31.2304,
            "address": state["destination"],
        }

    travel_interests = state.get("interests", [])
    logger.info(f"Travel interests: {travel_interests}")
    tags = get_attraction_tags_for_interests(travel_interests)
    logger.info(f"Attraction tags: {tags}")

    # Step 2: Search for attractions
    try:
        search_result = await search_attractions_nearby(
            nacos_naming=state["nacos_naming"],
            center_longitude=float(destination_coords.get("longitude") or 0),  # type: ignore[arg-type]
            center_latitude=float(destination_coords.get("latitude") or 0),  # type: ignore[arg-type]
            radius_km=25.0,
            tags=tags,
            limit=35,
        )
        # shuffle the attractions and sample 10
        attractions: list[AttractionDetail] = random.sample(
            search_result.attractions, 15
        )
        logger.info(f"Found {len(attractions)} attractions via gRPC service")
    except Exception as e:
        logger.error(f"Attraction search failed: {e}")
        attractions = []

    # Step 3: Use LLM to create complete itinerary
    class DailyActivity(BaseModel):
        name: str
        description: str
        category: str
        start_time: str  # HH:MM
        end_time: str
        estimated_cost: float

    class DailyPlan(BaseModel):
        day_number: int
        activities: list[DailyActivity]
        notes: str = ""

    class CompleteItineraryPlan(BaseModel):
        destination_info: str
        day_plans: list[DailyPlan]
        highlights: list[str]
        total_estimated_cost: float

    # Format attractions for LLM
    if len(attractions) > 0:
        attractions_text = "\n".join(
            [
                f"- {attraction.name}: {attraction.description} "
                f"(Tags: {', '.join(attraction.tags)})"
                for attraction in attractions[:10]
            ]
        )
    else:
        attractions_text = "No specific attractions found - generate general activities"

    interests_str = ", ".join(state.get("interests", [])) or "general travel"
    pace = state.get("pace", "moderate")

    # Adjust activities per day based on pace
    pace_activities = {"relaxed": 2, "moderate": 3, "intense": 4}
    activities_per_day = pace_activities.get(pace, 3)

    structured_llm = chat_model.with_structured_output(CompleteItineraryPlan)  # pyright: ignore

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
        itinerary_plan = CompleteItineraryPlan.model_validate(itinerary_plan)

        # Store attraction details for coordinate lookup
        attraction_details = {
            attraction.name: attraction.model_dump() for attraction in attractions
        }

        # Convert to expected format
        daily_schedule = {}
        for day_plan in itinerary_plan.day_plans:
            daily_schedule[day_plan.day_number] = [
                {
                    "name": activity.name,
                    "start_time": activity.start_time,
                    "end_time": activity.end_time,
                    "description": activity.description,
                    "category": activity.category,
                    "location": activity.name,  # Will be geocoded later
                    "estimated_cost": activity.estimated_cost,
                }
                for activity in day_plan.activities
            ]

        # Step 4: Geometric center of planned attractions -> search hotels nearby
        lats: list[float] = []
        lons: list[float] = []
        for day_plan in itinerary_plan.day_plans:
            for activity in day_plan.activities:
                att = _find_matching_attraction(activity.name, attraction_details)
                if att:
                    lats.append(att["latitude"])
                    lons.append(att["longitude"])
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
        else:
            center_lat = destination_coords["latitude"]
            center_lon = destination_coords["longitude"]

        hotel_limit = (
            3 if num_days <= 4 else 5
        )  # Short trip: one hotel; longer: multiple options
        try:
            hotel_result = await search_hotels_nearby(
                nacos_naming=state["nacos_naming"],
                center_longitude=center_lon,
                center_latitude=center_lat,
                radius_km=12.0,
                limit=hotel_limit,
            )
            hotel_details = [h.model_dump() for h in hotel_result.hotels]
            logger.info(
                "Found %d hotels near attractions center (%.4f, %.4f)",
                len(hotel_details),
                center_lat,
                center_lon,
            )
        except Exception as e:
            logger.error("Hotel search failed: %s", e)
            hotel_details = []

    except Exception as e:
        logger.error(f"LLM planning failed: {e}")
        # Create fallback plan
        attraction_details = {}
        daily_schedule = {}
        itinerary_plan = CompleteItineraryPlan(
            destination_info=f"General information about {state['destination']}",
            day_plans=[],
            highlights=[f"Explore {state['destination']}", "Experience local culture"],
            total_estimated_cost=0.0,
        )
        # Still search hotels by destination center
        try:
            hotel_result = await search_hotels_nearby(
                nacos_naming=state["nacos_naming"],
                center_longitude=destination_coords["longitude"],
                center_latitude=destination_coords["latitude"],
                radius_km=12.0,
                limit=5,
            )
            hotel_details = [h.model_dump() for h in hotel_result.hotels]
        except Exception as eh:
            logger.error("Hotel search failed: %s", eh)
            hotel_details = []

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
    """Find matching attraction using exact match first, then fuzzy match."""
    # 1. Exact match
    if location_name in attraction_details:
        return attraction_details[location_name]

    # 2. Case-insensitive match
    location_lower = location_name.lower()
    for name, details in attraction_details.items():
        if name.lower() == location_lower:
            return details

    # 3. Partial match (location_name contains attraction name or vice versa)
    for name, details in attraction_details.items():
        if name in location_name or location_name in name:
            logger.debug(f"Fuzzy matched '{location_name}' -> '{name}'")
            return details

    # 4. Partial match case-insensitive
    for name, details in attraction_details.items():
        if name.lower() in location_lower or location_lower in name.lower():
            logger.debug(
                f"Fuzzy matched (case-insensitive) '{location_name}' -> '{name}'"
            )
            return details

    return None


async def finalize_itinerary(state: PlanningState) -> dict[str, Any]:
    """Step 2: Finalize the itinerary with proper data structures."""
    logger.info("Finalizing itinerary with proper data structures")

    # Calculate dates
    start = datetime.fromisoformat(state["start_date"])
    end = datetime.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    attraction_details = state.get("attraction_details", {})
    daily_schedule = state.get("daily_schedule", {})
    hotel_details: list[dict[str, Any]] = state.get("hotel_details", [])

    # Assign which hotel for each night: short trip 1 hotel, longer trip can use multiple
    def _hotel_for_night(night_index: int) -> dict[str, Any] | None:
        if not hotel_details:
            return None
        if len(hotel_details) == 1:
            return hotel_details[0]
        # Spread multiple hotels over nights (e.g. 6 days -> hotel0 for nights 0,1,2 and hotel1 for 3,4,5)
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
        date = (start + timedelta(days=day_num - 1)).isoformat()
        daily_activities = daily_schedule.get(day_num, [])

        formatted_activities: list[Activity] = []
        for activity_data in daily_activities:
            activity_name = activity_data.get("name", "Activity")
            location_name = activity_data.get("location", activity_name)

            # Try to get real coordinates from
            # stored attraction details (with fuzzy matching)
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
                attraction_id = attraction_info.get("id")
            else:
                # Fallback: use destination coordinates directly (avoid extra geocoding)
                logger.info(
                    f"No matching attraction for '{location_name}',"
                    " using destination coords"
                )
                dest_coords = state.get("destination_coords", {})
                location = ActivityLocation(
                    name=location_name,
                    latitude=dest_coords.get("latitude", 31.2304),
                    longitude=dest_coords.get("longitude", 121.4737),
                    address=dest_coords.get("address", location_name),
                )
                attraction_id = None

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
                kind="attraction_visit",
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
            date=date,
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
