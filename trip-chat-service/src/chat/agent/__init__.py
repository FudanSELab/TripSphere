import os
import warnings

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from ag_ui_adk import AGUIToolset  # type: ignore
from google.adk.agents import LlmAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.llm_agent import ToolUnion  # pyright: ignore
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.load_memory_tool import load_memory_tool
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from chat.agent.agui import HotelViewingToolset
from chat.config.settings import get_settings
from chat.prompts.agent import DELEGATOR_INSTRUCTION

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module=".*")


def _ensure_openai_env() -> None:
    """Ensure OpenAI environment variables are set from application settings."""
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url


_ensure_openai_env()


def create_agent(
    agui_toolset: bool = False, sub_agents: list[BaseAgent] | None = None
) -> LlmAgent:
    sub_agents = sub_agents or []
    # NOTE: https://github.com/ag-ui-protocol/ag-ui/issues/1264
    weather_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python", args=["-m", "mcp_weather_server", "--debug"]
            ),
            timeout=10,  # 10 seconds timeout
        )
    )
    tools: list[ToolUnion] = [load_memory_tool, weather_toolset]  # pyright: ignore
    if agui_toolset is True:
        tools.extend([AGUIToolset(), HotelViewingToolset()])  # pyright: ignore
    return LlmAgent(
        name="chat",
        model=LiteLlm(model="openai/gpt-4o"),
        instruction=DELEGATOR_INSTRUCTION,
        sub_agents=sub_agents,
        tools=tools,
        # before_model_callback=_inject_agui_context,
    )


def create_adk_app(root_agent: BaseAgent) -> App:
    return App(
        name="chat",
        root_agent=root_agent,
        plugins=[],
        # Set the resumability config to enable resumability.
        resumability_config=ResumabilityConfig(is_resumable=True),
    )


"""
Use the following command to run ADK Web UI:

```
uv run adk web --log_level debug src/
```
"""
order_assistant = RemoteA2aAgent(
    name="order_assistant",
    agent_card=(
        f"http://localhost:24211/a2a/order_assistant{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)
root_agent = create_agent(False, sub_agents=[order_assistant])
app = create_adk_app(root_agent)
