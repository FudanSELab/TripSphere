import logging
import os
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from agent import ReviewSummarizerAgent
from agent_executor import ReviewSummarizerAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option('--host', 'host', default='0.0.0.0')
@click.option('--port', 'port', default=9376)
def main(host, port):
    """Starts the Review Summarizer Agent server."""
    try:
        if not os.getenv('TOOL_LLM_URL'):
            raise MissingAPIKeyError(
                'TOOL_LLM_URL environment variable not set.'
            )
        if not os.getenv('TOOL_LLM_NAME'):
            raise MissingAPIKeyError(
                'TOOL_LLM_NAME environment not variable not set.'
            )

        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        skill = AgentSkill(
            id='summarize_reviews',
            name='Review Summarization Tool',
            description='Helps with summarizing customer reviews for attractions and businesses',
            tags=['review summarization', 'business reviews', 'attraction reviews'],
            examples=['Summarize the reviews for Eiffel Tower', 'What do people think about Disneyland?', 'Can you provide a summary of reviews for this restaurant?'],
        )
        agent_card = AgentCard(
            name='Review Summarizer Agent',
            description='Analyzes customer reviews and provides concise summaries that answer user questions about businesses and attractions',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )


        # --8<-- [start:DefaultRequestHandler]
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=push_config_store)
        request_handler = DefaultRequestHandler(
            agent_executor=ReviewSummarizerAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender= push_sender
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)
        # --8<-- [end:DefaultRequestHandler]

    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()



