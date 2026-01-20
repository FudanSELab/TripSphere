import logging
import warnings

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from starlette.applications import Starlette

from journey_assistant.agent import agent_card, get_root_agent
from journey_assistant.config.settings import get_settings
from journey_assistant.config.telemetry import instrument_starlette, setup_telemetry
from journey_assistant.nacos.ai import NacosAI

warnings.filterwarnings("ignore")  # Suppress ADK Experimental Warnings

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry auto-instrumentation
# This should be done early, before creating the Starlette app
setup_telemetry(service_name="trip-journey-assistant")


def create_app() -> Starlette:
    # Get the A2A Starlette app
    a2a_app = to_a2a(get_root_agent(), agent_card=agent_card)

    # Instrument Starlette for automatic tracing
    # This enables auto-extraction of trace context from HTTP headers
    instrument_starlette(a2a_app)

    # Wrap the existing startup events with our lifespan logic
    original_startup = a2a_app.router.on_startup
    original_shutdown = a2a_app.router.on_shutdown

    async def combined_startup() -> None:
        # Run original A2A startup events
        for handler in original_startup:
            await handler()

        # Run our custom startup logic
        settings = get_settings()
        logger.info(f"Loaded settings: {settings}")

        try:
            a2a_app.state.nacos_ai = await NacosAI.create_nacos_ai(
                agent_name=agent_card.name,
                port=settings.uvicorn.port,
                server_address=settings.nacos.server_address,
            )
            # Release A2A AgentCard to Nacos AI Service
            await a2a_app.state.nacos_ai.release_agent_card(agent_card)
            logger.info("Registering agent endpoint...")
            await a2a_app.state.nacos_ai.register(agent_card.version)

        except Exception as e:
            logger.error(f"Error during startup: {e}")
            raise

    async def combined_shutdown() -> None:
        # Run our custom shutdown logic first
        logger.info("Deregistering agent endpoint...")
        if isinstance(a2a_app.state.nacos_ai, NacosAI):
            await a2a_app.state.nacos_ai.deregister(agent_card.version)
            await a2a_app.state.nacos_ai.shutdown()

        # Run original A2A shutdown events
        for handler in original_shutdown:
            await handler()

    # Replace the startup/shutdown handlers
    a2a_app.router.on_startup = [combined_startup]
    a2a_app.router.on_shutdown = [combined_shutdown]

    return a2a_app


app = create_app()
