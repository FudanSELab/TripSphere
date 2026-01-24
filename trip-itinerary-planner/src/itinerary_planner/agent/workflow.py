import logging

from langgraph.graph import END, START, StateGraph  # pyright: ignore
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore

from itinerary_planner.agent.nodes import finalize_itinerary, research_and_plan
from itinerary_planner.agent.state import PlanningState

logger = logging.getLogger(__name__)


def create_planning_workflow() -> CompiledStateGraph[
    PlanningState, None, PlanningState, PlanningState
]:
    """Create and compile the itinerary planning workflow.

    This workflow follows a streamlined 2-step process:
    1. Research and Plan (70%) - Research destination, find attractions, create schedule
    2. Finalize Itinerary (100%) - Convert to proper data structures with coordinates

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating simplified planning workflow")

    # Create workflow with PlanningState
    workflow = StateGraph[PlanningState, None, PlanningState, PlanningState](
        PlanningState
    )

    # Add nodes for each step
    workflow.add_node("research_and_plan", research_and_plan)  # pyright: ignore
    workflow.add_node("finalize_itinerary", finalize_itinerary)  # pyright: ignore

    # Define linear flow
    workflow.add_edge(START, "research_and_plan")
    workflow.add_edge("research_and_plan", "finalize_itinerary")
    workflow.add_edge("finalize_itinerary", END)

    # Compile the workflow
    graph = workflow.compile()  # pyright: ignore

    logger.info("Planning workflow compiled successfully")
    return graph
