import os
import warnings

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from ag_ui_adk import AGUIToolset  # pyright: ignore  # noqa: F401
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.load_memory_tool import load_memory_tool
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from chat.config.settings import get_settings
from chat.prompts.agent import DELEGATOR_INSTRUCTION

warnings.filterwarnings("ignore", module="google.adk")

openai_settings = get_settings().openai
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
if not os.environ.get("OPENAI_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = openai_settings.base_url


# NOTE: Wait for AGUI to fix the deep copy issue of McpToolset with StdioConnectionParams.
def create_weather_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python", args=["-m", "mcp_weather_server"]
            )
        )
    )


def create_agent(agui: bool = False) -> LlmAgent:
    order_assistant = RemoteA2aAgent(
        name="order_assistant",
        agent_card=(
            f"http://localhost:8000/a2a/order_assistant{AGENT_CARD_WELL_KNOWN_PATH}"
        ),
    )
    return LlmAgent(
        name="chat",
        model=LiteLlm(model="openai/gpt-4o"),
        instruction=DELEGATOR_INSTRUCTION,
        sub_agents=[order_assistant],
        tools=[load_memory_tool, AGUIToolset()],
    )


root_agent = create_agent()

app = App(
    name="chat",
    root_agent=root_agent,
    # Set the resumability config to enable resumability.
    resumability_config=ResumabilityConfig(is_resumable=True),
)
