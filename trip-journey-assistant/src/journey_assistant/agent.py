import logging
import os
from datetime import datetime
from functools import lru_cache
from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from journey_assistant.config.settings import get_settings

logger = logging.getLogger(__name__)


AGENT_NAME = "journey_assistant"
AGENT_DESCRIPTION = (
    "An agent that can help users with journey information, such as weather details."
)
INSTRUCTION = """Role: You are a helpful journey assistant agent.

Capabilities:
- You are integrated with weather information tools.

Current Datetime (with Timezone): {current_datetime}"""


def root_instruction(_: ReadonlyContext) -> str:
    # Get current datetime with timezone
    current_datetime = datetime.now().astimezone().isoformat()
    return INSTRUCTION.format(current_datetime=current_datetime)


@lru_cache(maxsize=1, typed=True)
def get_root_agent(model: str = "openai/gpt-4o-mini") -> LlmAgent:
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL", None):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url

    weather_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python", args=["-m", "mcp_weather_server"]
            )
        )
    )
    return LlmAgent(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        model=LiteLlm(model=model),
        instruction=root_instruction,
        tools=[weather_toolset],
    )


weather_info = AgentSkill(
    id="weather_information",
    name="Weather Information",
    description="Provides weather information for travel destinations.",
    tags=["weather"],
    examples=["How's the weather in Shanghai tomorrow?"],
)
agent_card = AgentCard(
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    version=version("journey-assistant"),
    # If no endpoint is available in the current version,
    # this URL will be used by Nacos AI service.
    url=f"http://localhost:{get_settings().uvicorn.port}",
    skills=[weather_info],
    capabilities=AgentCapabilities(),
    default_input_modes=["text"],
    default_output_modes=["text"],
)
