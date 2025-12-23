"""Node functions for the itinerary planning workflow."""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from itinerary_planner._planning.state import ItineraryState, Question
from itinerary_planner.config.settings import get_settings

logger = logging.getLogger(__name__)


settings = get_settings()


def get_llm() -> ChatOpenAI:
    """Get configured LLM instance."""
    llm_kwargs: dict[str, Any] = {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "api_key": settings.openai.api_key.get_secret_value(),
    }

    # Add base_url if configured
    if settings.openai.base_url:
        llm_kwargs["base_url"] = settings.openai.base_url

    return ChatOpenAI(**llm_kwargs)


async def research_destination(state: ItineraryState) -> dict[str, Any]:
    """Research the destination to gather relevant information."""
    logger.info(f"Researching destination: {state['destination']}")

    llm = get_llm()

    messages = [
        SystemMessage(
            content=(
                "You are a knowledgeable travel expert with deep knowledge of destinations worldwide."
            )
        ),
        HumanMessage(
            content=f"""Provide a comprehensive overview of {state["destination"]} \
for trip planning.
Include:
1. Top attractions and landmarks
2. Local cuisine and dining options
3. Cultural considerations and customs
4. Best areas to stay
5. Transportation options
6. Weather considerations for {state["start_date"]} to {state["end_date"]}

Focus on aspects relevant to these interests: {", ".join(state["interests"])}
Budget level: {state["budget_level"]}
"""
        ),
    ]

    response = await llm.ainvoke(messages)
    destination_info = str(response.content)

    logger.info(f"Destination research completed for {state['destination']}")
    return {"destination_info": destination_info}


async def suggest_activities(state: ItineraryState) -> dict[str, Any]:
    """Generate activity suggestions based on destination research and preferences."""
    logger.info(f"Generating activity suggestions for {state['destination']}")

    llm = get_llm()

    # Calculate number of days
    start = datetime.fromisoformat(state["start_date"])
    end = datetime.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    messages = [
        SystemMessage(
            content=(
                "You are an expert travel planner. Generate activity suggestions in JSON format.\nEach activity should include: name, description, category, estimated_duration_hours, estimated_cost, location, time_of_day_preference."
            )
        ),
        HumanMessage(
            content=f"""Based on this destination information:
{state["destination_info"]}

Generate {num_days * 4} diverse activity suggestions for a \
{num_days}-day trip to {state["destination"]}.

Traveler preferences:
- Interests: {", ".join(state["interests"])}
- Budget level: {state["budget_level"]}
- Number of travelers: {state["num_travelers"]}

Provide the activities as a JSON array. Each activity should have:
- name: string
- description: string
- category: string (sightseeing, dining, activity, entertainment, shopping, cultural)
- estimated_duration_hours: number
- estimated_cost: number (per person in USD)
- location: string (address or area)
- time_of_day_preference: string (morning, afternoon, evening, any)

Return ONLY the JSON array, no additional text.
"""
        ),
    ]

    response = await llm.ainvoke(messages)
    response_text = str(response.content).strip()

    # Try to extract JSON from response
    try:
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        activity_suggestions = json.loads(response_text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON response, using fallback")
        activity_suggestions = []

    logger.info(f"Generated {len(activity_suggestions)} activity suggestions")
    return {"activity_suggestions": activity_suggestions}


async def create_daily_schedule(state: ItineraryState) -> dict[str, Any]:
    """Organize activities into a day-by-day schedule."""
    logger.info("Creating daily schedule")

    llm = get_llm()

    # Calculate dates
    start = datetime.fromisoformat(state["start_date"])
    end = datetime.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    # Create date list
    dates = [(start + timedelta(days=i)).isoformat() for i in range(num_days)]

    messages = [
        SystemMessage(
            content=(
                "You are an expert at creating optimal daily travel itineraries.\nCreate a balanced schedule that considers timing, location proximity, and traveler energy levels.\nReturn your response as a JSON object mapping day numbers to activity lists."
            )
        ),
        HumanMessage(
            content=f"""Create a {num_days}-day itinerary for {state["destination"]}.

Available activities:
{json.dumps(state["activity_suggestions"], indent=2)}

Requirements:
- Organize 3-5 activities per day
- Consider logical flow and proximity
- Balance activity intensity throughout the day
- Include meal times
- Account for travel time between locations
- Start days around 9 AM, end around 9 PM

Dates: {", ".join(dates)}

Return a JSON object with this structure:
{{
  "1": [
    {{
      "activity_name": "...",
      "start_time": "09:00",
      "end_time": "11:00",
      "description": "...",
      "category": "...",
      "location": "...",
      "estimated_cost": 0
    }}
  ],
  "2": [...],
  ...
}}

Return ONLY the JSON object, no additional text.
"""
        ),
    ]

    response = await llm.ainvoke(messages)
    response_text = str(response.content).strip()

    # Try to extract JSON from response
    try:
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        daily_schedule_data = json.loads(response_text)
        # Convert string keys to integers
        daily_schedule = {int(k): v for k, v in daily_schedule_data.items()}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse daily schedule JSON, creating simple fallback")
        daily_schedule = {}

    logger.info(f"Created schedule for {len(daily_schedule)} days")
    return {"daily_schedule": daily_schedule}


async def finalize_itinerary(state: ItineraryState) -> dict[str, Any]:
    """Create the final itinerary structure with all details."""
    logger.info("Finalizing itinerary")

    # Calculate dates
    start = datetime.fromisoformat(state["start_date"])
    end = datetime.fromisoformat(state["end_date"])
    num_days = (end - start).days + 1

    # Build day plans
    day_plans = []
    total_cost = 0.0
    total_activities = 0

    for day_num in range(1, num_days + 1):
        date = (start + timedelta(days=day_num - 1)).isoformat()
        activities = state["daily_schedule"].get(day_num, [])

        formatted_activities = []
        for idx, activity in enumerate(activities):
            activity_cost = activity.get("estimated_cost", 0)
            total_cost += activity_cost * state["num_travelers"]
            total_activities += 1

            formatted_activities.append(
                {
                    "id": f"act_{day_num}_{idx}",
                    "name": activity.get("activity_name", "Activity"),
                    "description": activity.get("description", ""),
                    "start_time": activity.get("start_time", ""),
                    "end_time": activity.get("end_time", ""),
                    "location": {
                        "name": activity.get("location", ""),
                        "latitude": 0.0,
                        "longitude": 0.0,
                        "address": activity.get("location", ""),
                    },
                    "category": activity.get("category", "activity"),
                    "cost": {
                        "amount": activity_cost,
                        "currency": "USD",
                    },
                }
            )

        day_plans.append(
            {
                "day_number": day_num,
                "date": date,
                "activities": formatted_activities,
                "notes": f"Day {day_num} in {state['destination']}",
            }
        )

    # Generate highlights
    llm = get_llm()
    messages = [
        SystemMessage(
            content="You are a travel expert. Create concise, exciting highlights."
        ),
        HumanMessage(
            content=f"""Summarize the top 3-5 highlights of this {num_days}-day \
trip to {state["destination"]}.
            
Activities: {json.dumps(state["daily_schedule"], indent=2)}

Return a JSON array of strings, each being a one-sentence highlight.
Example: ["Visit the iconic Eiffel Tower at sunrise", \
"Enjoy authentic French cuisine in Le Marais"]

Return ONLY the JSON array.
"""
        ),
    ]

    response = await llm.ainvoke(messages)
    response_text = str(response.content).strip()

    try:
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        highlights = json.loads(response_text)
    except json.JSONDecodeError:
        highlights = [f"Explore {state['destination']}", "Discover local culture"]

    # Generate itinerary ID
    itinerary_id = f"itin_{state['user_id']}_{datetime.now().timestamp()}"
    now_iso = datetime.now().isoformat()

    itinerary = {
        "id": itinerary_id,
        "destination": state["destination"],
        "start_date": state["start_date"],
        "end_date": state["end_date"],
        "day_plans": day_plans,
        "summary": {
            "total_estimated_cost": total_cost,
            "currency": "USD",
            "total_activities": total_activities,
            "highlights": highlights,
        },
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    logger.info(f"Finalized itinerary {itinerary_id}")
    return {"itinerary": itinerary, "error": None}


async def check_need_clarification(state: ItineraryState) -> dict[str, Any]:
    """Check if we need to ask the user for clarification or additional information."""
    logger.info("Checking if clarification is needed")

    llm = get_llm()

    # Check if interests are too vague or if we need more specific information
    messages = [
        SystemMessage(
            content=(
                "You are an expert travel planner assistant. Analyze the "
                "user's travel request and determine if you need additional "
                "information to create a better itinerary.\n\n"
                "Consider:\n"
                "1. Are the interests too vague or general?\n"
                "2. Are there specific preferences we should know about "
                "(dietary restrictions, mobility issues, etc.)?\n"
                "3. Is the budget level clear enough?\n"
                "4. Do we need to know about specific must-see attractions?\n"
                "5. Should we know about the travel style "
                "(relaxed vs. packed schedule)?\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "needs_clarification": true/false,\n'
                '  "question": "Your question here if needs_clarification '
                'is true",\n'
                '  "suggested_answers": ["option1", "option2", ...] '
                "// Optional\n"
                "}"
            )
        ),
        HumanMessage(
            content=f"""Analyze this travel request:
- Destination: {state["destination"]}
- Dates: {state["start_date"]} to {state["end_date"]}
- Interests: {", ".join(state["interests"])}
- Budget level: {state["budget_level"]}
- Number of travelers: {state["num_travelers"]}
- Preferences: {state["preferences"]}
- User responses so far: {state.get("user_responses", {})}

Destination info gathered:
{state.get("destination_info", "Not yet gathered")}

Do we need to ask the user for additional information? If so, what should we ask?
Return ONLY a JSON object."""
        ),
    ]

    response = await llm.ainvoke(messages)
    response_text = str(response.content).strip()

    try:
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        clarification_check = json.loads(response_text)

        if clarification_check.get("needs_clarification", False):
            question_id = str(uuid.uuid4())
            question: Question = {
                "question_id": question_id,
                "question_text": clarification_check.get(
                    "question", "Could you provide more details?"
                ),
                "suggested_answers": clarification_check.get("suggested_answers", []),
                "requires_answer": True,
            }

            logger.info(f"Generated question: {question['question_text']}")
            return {
                "pending_question": question,
                "needs_user_input": True,
            }
        else:
            logger.info("No clarification needed, proceeding with planning")
            return {
                "pending_question": None,
                "needs_user_input": False,
            }

    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse clarification check, proceeding without questions"
        )
        return {
            "pending_question": None,
            "needs_user_input": False,
        }


async def incorporate_user_response(state: ItineraryState) -> dict[str, Any]:
    """Incorporate the user's response into the planning context."""
    logger.info("Incorporating user response")

    # The user response should already be in state['user_responses']
    # We just need to clear the pending question and flag
    return {
        "pending_question": None,
        "needs_user_input": False,
    }
