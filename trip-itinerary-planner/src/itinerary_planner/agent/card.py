from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from itinerary_planner.config.settings import get_settings

itinerary_planning = AgentSkill(
    id="itinerary_planning",
    name="Itinerary Planning",
    description=(
        "Plan complete multi-day itineraries with day-by-day schedules and activities."
    ),
    tags=["itinerary", "travel"],
)
agent_card = AgentCard(
    name="itinerary_planner",
    description=(
        "Travel itinerary planner that creates personalized multi-day trip plans"
        " based on user preferences, interests, and budget."
    ),
    version=version("itinerary-planner"),
    url=f"http://localhost:{get_settings().uvicorn.port}",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[itinerary_planning],
)
