import logging
import os
import warnings
from datetime import datetime
from functools import lru_cache
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.long_running_tool import LongRunningFunctionTool
from google.adk.tools.tool_context import ToolContext

from order_assistant.config.settings import get_settings
from order_assistant.tools.order import OrderToolset
from order_assistant.tools.order_draft import OrderDraftToolset
from order_assistant.tools.product import ProductToolset

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", module="google.adk")

AGENT_NAME = "order_assistant"
AGENT_DESCRIPTION = "An agent that can help users with their orders."
INSTRUCTION = """Role: You are a helpful order management assistant agent.

**Order placing process:**
1. Create an order draft if not exists
2. Add SKUs (attractions/hotel rooms/...) to the draft
3. Submit the order draft to create the real order

**Order cancellation process:**
1. Ask user for confirmation for the order cancellation
2. If confirmed, cancel the order
3. If not confirmed, do not cancel the order

Note: Always respond one textual final response at the end of each turn.

Current Datetime (with Timezone): {current_datetime}
"""


def root_instruction(_: ReadonlyContext) -> str:
    # Get current datetime with timezone
    current_datetime = datetime.now().astimezone().isoformat()
    return INSTRUCTION.format(current_datetime=current_datetime)


def ask_for_confirmation(
    order_id: str, reason: str, tool_context: ToolContext
) -> dict[str, Any]:
    """Ask user for confirmation for the order cancellation."""
    return {"status": "pending", "order_id": order_id, "reason": reason}


@lru_cache(maxsize=1, typed=True)
def get_root_agent(model: str = "openai/gpt-4o") -> LlmAgent:
    settings = get_settings()
    if not os.environ.get("OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = settings.openai.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL", None):
        os.environ["OPENAI_BASE_URL"] = settings.openai.base_url

    return LlmAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        model=LiteLlm(model=model),
        instruction=root_instruction,
        tools=[
            OrderToolset(),
            ProductToolset(),
            OrderDraftToolset(),
            LongRunningFunctionTool(func=ask_for_confirmation),
        ],
    )


root_agent = get_root_agent()
