import logging

from langgraph.graph import END, START, StateGraph  # pyright: ignore
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore

from itinerary_planner.agent.nodes import (
    finalize_itinerary,
    generate_markdown,
    research_and_plan,
)
from itinerary_planner.agent.state import PlanningState

logger = logging.getLogger(__name__)


def create_planning_workflow() -> CompiledStateGraph[
    PlanningState, None, PlanningState, PlanningState
]:
    """Create and compile the itinerary planning workflow.

    3-step linear process:
    1. Research and Plan (70%) — Research destination, find attractions, create schedule
    2. Finalize Itinerary (85%) — Convert to proper data structures with coordinates
    3. Generate Markdown (100%) — Produce natural-language Markdown itinerary
    """
    logger.info("Creating planning workflow")

    workflow = StateGraph[PlanningState, None, PlanningState, PlanningState](
        PlanningState
    )

    workflow.add_node("research_and_plan", research_and_plan)  # pyright: ignore
    workflow.add_node("finalize_itinerary", finalize_itinerary)  # pyright: ignore
    workflow.add_node("generate_markdown", generate_markdown)  # pyright: ignore

    workflow.add_edge(START, "research_and_plan")
    workflow.add_edge("research_and_plan", "finalize_itinerary")
    workflow.add_edge("finalize_itinerary", "generate_markdown")
    workflow.add_edge("generate_markdown", END)

    graph = workflow.compile()  # pyright: ignore

    logger.info("Planning workflow compiled successfully")
    return graph
