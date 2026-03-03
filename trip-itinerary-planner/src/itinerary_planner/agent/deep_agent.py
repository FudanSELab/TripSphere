import logging
import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from itinerary_planner.config.settings import get_settings
from itinerary_planner.prompts.deep_agent import DEEP_AGENT_INSTRUCTION

logger = logging.getLogger(__name__)


def _ensure_openai_env() -> None:
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url


def create_deep_agent(model: str = "openai/gpt-4o-mini") -> LlmAgent:
    """Create the Deep Agent for conversational itinerary modification.

    This agent does not define its own tools. Instead, it receives tool
    definitions from CopilotKit via useCopilotAction on the frontend.
    CopilotKit injects these tools into the AG-UI protocol automatically.
    """
    _ensure_openai_env()

    agent = LlmAgent(
        name="itinerary_deep_agent",
        model=LiteLlm(model=model),
        instruction=DEEP_AGENT_INSTRUCTION,
    )

    logger.info("Deep Agent created: %s (model=%s)", agent.name, model)
    return agent
