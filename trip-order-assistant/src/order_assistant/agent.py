import logging
import os
from datetime import datetime
from functools import lru_cache
from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm

from order_assistant.config.settings import get_settings
from order_assistant.tools.order import OrderToolset
from order_assistant.tools.product import ProductToolset

logger = logging.getLogger(__name__)


AGENT_NAME = "order_assistant"
AGENT_DESCRIPTION = "An agent that can help users with their orders."
INSTRUCTION = """Role: You are a helpful order management assistant agent.

Capabilities:
- You are equipped with order management tools.
- You are equipped with product information tools.

Current Datetime (with Timezone): {current_datetime}
"""


def root_instruction(_: ReadonlyContext) -> str:
    # Get current datetime with timezone
    current_datetime = datetime.now().astimezone().isoformat()
    return INSTRUCTION.format(current_datetime=current_datetime)


@lru_cache(maxsize=1, typed=True)
def get_root_agent(model: str = "openai/gpt-4o-mini") -> LlmAgent:
    settings = get_settings()
    if not os.environ.get("OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = settings.openai.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL", None):
        os.environ["OPENAI_BASE_URL"] = settings.openai.base_url

    order_toolset = OrderToolset()
    product_toolset = ProductToolset()
    return LlmAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        model=LiteLlm(model=model),
        instruction=root_instruction,
        tools=[order_toolset, product_toolset],
    )


manage_order = AgentSkill(
    id="manage_order",
    name="Manage Order",
    description="Manages orders like creating, getting, and canceling them.",
    tags=["create order", "get order", "cancel order"],
    examples=["Get the details of an order with ID 1234567890."],
)
agent_card = AgentCard(
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    version=version("order-assistant"),
    # If no endpoint is available in the current version,
    # this URL will be used by Nacos AI service.
    url=f"http://localhost:{get_settings().uvicorn.port}",
    skills=[manage_order],
    capabilities=AgentCapabilities(),
    default_input_modes=["text"],
    default_output_modes=["text"],
)


root_agent = get_root_agent()
