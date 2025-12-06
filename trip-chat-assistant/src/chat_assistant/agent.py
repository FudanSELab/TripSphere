import logging
from datetime import datetime

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

load_dotenv()


def fetch_weather(location: str, timestamp: datetime | None = None) -> str:
    """
    Fetches weather information for a given location at a specific timestamp.

    Arguments:
        location: The location to get the weather for.
        timestamp: Optional datetime for which to get the weather.
            Defaults to the current datetime.

    Returns:
        A string describing the weather at the location and time.
    """
    # Placeholder implementation
    if timestamp is None:
        timestamp = datetime.now()
    print(f"Fetching weather for {location} at {timestamp}")
    return f" {location} is sunny with a temperature of 25℃ at {timestamp}."


agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o-mini"),
    name="chat_assistant",
    description="An agent that can help with weather information.",
    instruction="Use the fetch_weather tool to get weather information.",
    tools=[fetch_weather],
)
app = to_a2a(agent)
