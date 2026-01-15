import logging
import warnings
from datetime import datetime
from importlib.metadata import version

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from journey_assistant.config.settings import get_settings

warnings.filterwarnings("ignore")  # Suppress ADK Experimental Warnings

load_dotenv()

logger = logging.getLogger(__name__)

settings = get_settings()

weather_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python", args=["-m", "mcp_weather_server"]
        )
    )
)


INSTRUCTION = """
Role: You are a helpful journey assistant agent.

Capabilities:
- You are integrated with weather information tools.

Current Datetime (with Timezone): {current_datetime}
""".strip()

AGENT_NAME = "journey_assistant"

AGENT_DESCRIPTION = """
An agent that can help users with journey information, such as weather details.
""".strip()


def root_instruction(_: ReadonlyContext) -> str:
    # Get current datetime with timezone
    current_datetime = datetime.now().astimezone().isoformat()
    return INSTRUCTION.format(current_datetime=current_datetime)


root_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
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
    url=f"http://{settings.uvicorn.host}:{settings.uvicorn.port}",
    skills=[weather_info],
    capabilities=AgentCapabilities(),
    default_input_modes=["text"],
    default_output_modes=["text"],
)
app = to_a2a(root_agent, agent_card=agent_card)
