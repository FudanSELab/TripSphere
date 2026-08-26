import logging
from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from review_summary.config.settings import get_settings

logger = logging.getLogger(__name__)


summarize_reviews = AgentSkill(
    id="summarize_reviews",
    name="Review Summarization",
    description="Answers evidence-backed questions about hotel and attraction reviews.",
    tags=["review analysis", "hotel reviews", "attraction reviews"],
    examples=[
        "What do guests say about this hotel's location and service?",
        "What do people think about Shanghai Disneyland?",
    ],
)
agent_card = AgentCard(
    name="review_summary",
    description=(
        "Analyze ReviewService-backed hotel and attraction reviews and answer "
        "questions with structured source evidence."
    ),
    url=f"http://localhost:{get_settings().uvicorn.port}",
    version=version("review-summary"),
    default_input_modes=["text"],
    default_output_modes=["text", "application/json"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[summarize_reviews],
)
