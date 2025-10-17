"""LangGraph workflow for itinerary planning."""

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from itinerary_planner.planning.nodes import (
    create_daily_schedule,
    finalize_itinerary,
    research_destination,
    suggest_activities,
)
from itinerary_planner.planning.state import ItineraryState

logger = logging.getLogger(__name__)


def create_planning_workflow() -> StateGraph:
    """Create and configure the itinerary planning workflow.

    The workflow follows these steps:
    1. Research destination - Gather information about the destination
    2. Suggest activities - Generate relevant activity suggestions
    3. Create daily schedule - Organize activities into a coherent daily plan
    4. Finalize itinerary - Format and structure the final itinerary

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create workflow
    workflow = StateGraph(ItineraryState)

    # Add nodes
    workflow.add_node("research_destination", research_destination)
    workflow.add_node("suggest_activities", suggest_activities)
    workflow.add_node("create_daily_schedule", create_daily_schedule)
    workflow.add_node("finalize_itinerary", finalize_itinerary)

    # Define the flow
    workflow.set_entry_point("research_destination")
    workflow.add_edge("research_destination", "suggest_activities")
    workflow.add_edge("suggest_activities", "create_daily_schedule")
    workflow.add_edge("create_daily_schedule", "finalize_itinerary")
    workflow.add_edge("finalize_itinerary", END)

    # Compile the workflow
    app = workflow.compile()

    logger.info("Planning workflow created and compiled")
    return app


class ItineraryPlanner:
    """High-level interface for the itinerary planning workflow."""

    def __init__(self) -> None:
        """Initialize the planner with a compiled workflow."""
        self.workflow = create_planning_workflow()

    async def plan_itinerary(
        self,
        user_id: str,
        destination: str,
        start_date: str,
        end_date: str,
        interests: list[str],
        budget_level: str,
        num_travelers: int,
        preferences: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Plan a complete itinerary.

        Args:
            user_id: Unique identifier for the user
            destination: Destination city/country
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            interests: List of user interests
            budget_level: Budget level (budget/moderate/luxury)
            num_travelers: Number of travelers
            preferences: Additional preferences

        Returns:
            Complete itinerary dictionary
        """
        logger.info(f"Planning itinerary for {user_id} to {destination}")

        # Initialize state
        initial_state: ItineraryState = {
            "user_id": user_id,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "interests": interests,
            "budget_level": budget_level,
            "num_travelers": num_travelers,
            "preferences": preferences or {},
            "destination_info": "",
            "activity_suggestions": [],
            "daily_schedule": {},
            "itinerary": {},
            "error": None,
        }

        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)

            if result.get("error"):
                logger.error(f"Error during planning: {result['error']}")
                raise Exception(result["error"])

            logger.info(f"Successfully planned itinerary {result['itinerary']['id']}")
            return result["itinerary"]

        except Exception as e:
            logger.error(f"Failed to plan itinerary: {e}")
            raise

    async def refine_itinerary(
        self,
        itinerary_id: str,
        user_id: str,
        refinement_instructions: str,
        modifications: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Refine an existing itinerary based on user feedback.

        This is a simplified version that would need to fetch the existing
        itinerary and apply modifications. For now, it returns a placeholder.

        Args:
            itinerary_id: ID of the itinerary to refine
            user_id: User ID
            refinement_instructions: Natural language refinement instructions
            modifications: Structured modifications

        Returns:
            Refined itinerary dictionary
        """
        logger.info(f"Refining itinerary {itinerary_id} for user {user_id}")

        # TODO: Implement refinement logic
        # This would involve:
        # 1. Fetching the existing itinerary from storage
        # 2. Applying the requested modifications
        # 3. Re-running relevant parts of the workflow
        # 4. Updating and returning the refined itinerary

        raise NotImplementedError("Itinerary refinement not yet implemented")

