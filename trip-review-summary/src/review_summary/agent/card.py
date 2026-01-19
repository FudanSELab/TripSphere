import logging
from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from review_summary.config.settings import get_settings

logger = logging.getLogger(__name__)


summarize_reviews = AgentSkill(
    id="summarize_reviews",
    name="Review Summarization",
    description="Helps with summarizing reviews of attractions.",
    tags=["review summary", "attraction reviews"],
    examples=[
        "What do people think about Shanghai Disneyland?",
        "Can you provide a summary of reviews for West Lake?",
    ],
)
agent_card = AgentCard(
    name="review_summary",
    description=(
        "Analyze customer reviews and provide concise summaries "
        "that answer user questions about attractions."
    ),
    url=f"http://localhost:{get_settings().uvicorn.port}",
    version=version("review-summary"),
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[summarize_reviews],
)
