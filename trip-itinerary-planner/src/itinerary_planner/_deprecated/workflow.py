"""LangGraph workflow for itinerary planning."""

import logging
from typing import Any, Literal, cast

from itinerary_planner._planning.nodes import (
    check_need_clarification,
    create_daily_schedule,
    finalize_itinerary,
    incorporate_user_response,
    research_destination,
    suggest_activities,
)
from itinerary_planner._planning.state import ItineraryState
from langgraph.graph import END, StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.graph.state import (  # pyright: ignore[reportMissingTypeStubs]
    CompiledStateGraph,
)

logger = logging.getLogger(__name__)


def should_ask_user(state: ItineraryState) -> Literal["ask_question", "continue"]:
    """Determine if we should ask the user a question or continue."""
    if state.get("needs_user_input", False):
        return "ask_question"
    return "continue"


def create_planning_workflow() -> CompiledStateGraph[ItineraryState]:
    """Create and configure the itinerary planning workflow.

    The workflow follows these steps:
    1. Research destination - Gather information about the destination
    2. Check for clarification - Determine if we need additional user input
    3. [If needed] Ask question - Wait for user input
    4. Suggest activities - Generate relevant activity suggestions
    5. Create daily schedule - Organize activities into a coherent daily plan
    6. Finalize itinerary - Format and structure the final itinerary

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create workflow
    workflow = StateGraph[ItineraryState](ItineraryState)

    # Add nodes
    workflow.add_node("research_destination", research_destination)  # pyright: ignore
    workflow.add_node("check_clarification", check_need_clarification)  # pyright: ignore
    workflow.add_node(  # pyright: ignore
        "ask_question", lambda state: state
    )  # Placeholder for interruption
    workflow.add_node("incorporate_response", incorporate_user_response)  # pyright: ignore
    workflow.add_node("suggest_activities", suggest_activities)  # pyright: ignore
    workflow.add_node("create_daily_schedule", create_daily_schedule)  # pyright: ignore
    workflow.add_node("finalize_itinerary", finalize_itinerary)  # pyright: ignore

    # Define the flow
    workflow.set_entry_point("research_destination")
    workflow.add_edge("research_destination", "check_clarification")

    # Conditional edge: check if we need user input
    workflow.add_conditional_edges(
        "check_clarification",
        should_ask_user,
        {
            "ask_question": "ask_question",
            "continue": "suggest_activities",
        },
    )

    # After asking question, incorporate response and continue
    workflow.add_edge("ask_question", "incorporate_response")
    workflow.add_edge("incorporate_response", "suggest_activities")

    workflow.add_edge("suggest_activities", "create_daily_schedule")
    workflow.add_edge("create_daily_schedule", "finalize_itinerary")
    workflow.add_edge("finalize_itinerary", END)

    # Compile the workflow
    app = workflow.compile()  # type: ignore[misc]

    logger.info("Planning workflow created and compiled")
    return app  # type: ignore[return-value]


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
        """Plan a complete itinerary.

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
            "pending_question": None,
            "user_responses": {},
            "needs_user_input": False,
            "itinerary": {},
            "error": None,
        }

        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)  # type: ignore[misc]

            if result.get("error"):
                logger.error(f"Error during planning: {result['error']}")
                raise Exception(result["error"])

            logger.info(f"Successfully planned itinerary {result['itinerary']['id']}")
            return cast(dict[str, Any], result["itinerary"])

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
