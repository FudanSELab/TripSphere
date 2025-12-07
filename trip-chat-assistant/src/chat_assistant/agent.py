import logging
import warnings
from datetime import datetime

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

warnings.filterwarnings("ignore")  # Suppress ADK Experimental Warnings

load_dotenv()

logger = logging.getLogger(__name__)

weather_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python", args=["-m", "mcp_weather_server"]
        )
    )
)


INSTRUCTION = """
Role: You are a helpful agent integrated with weather information tools.

Current Datetime (with Timezone): {current_datetime}
""".strip()


def root_instruction(ctx: ReadonlyContext) -> str:
    # Get current datetime with timezone
    current_datetime = datetime.now().astimezone().isoformat()
    return INSTRUCTION.format(current_datetime=current_datetime)


root_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="chat_assistant",
    description="An agent that can help users with weather information.",
    instruction=root_instruction,
    tools=[weather_toolset],
)
app = to_a2a(root_agent)
