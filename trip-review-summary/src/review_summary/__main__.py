import logging
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
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from review_summary.agent.agent import ReviewSummarizerAgent
from review_summary.agent.agent_executor import ReviewSummarizerAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


# parser.add_argument("--query_chat_model", default="gpt-4o-2024-08-06", type=str)
# parser.add_argument("--embedding_model", default="text-embedding-3-large", type=str)


@click.command()
@click.option("--host", "host", default="0.0.0.0")
@click.option("--port", "port", default=9376)
def main(host, port):
    """Starts the Review Summarizer Agent server."""
    try:
        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        skill = AgentSkill(
            id="summarize_reviews",
            name="Review Summarization Tool",
            description="Helps with summarizing customer reviews for attractions and businesses",
            tags=["review summarization", "business reviews", "attraction reviews"],
            examples=[
                "Summarize the reviews for Eiffel Tower",
                "What do people think about Disneyland?",
                "Can you provide a summary of reviews for this restaurant?",
            ],
        )
        agent_card = AgentCard(
            name="review_summary",
            description="Analyzes customer reviews and provides concise summaries that answer user questions about businesses and attractions",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            default_input_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        # --8<-- [start:DefaultRequestHandler]
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client, config_store=push_config_store
        )
        query_chat_model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
        embedding_llm = OpenAIEmbeddings(model="text-embedding-3-large")
        request_handler = DefaultRequestHandler(
            agent_executor=ReviewSummarizerAgentExecutor(
                query_chat_model, embedding_llm
            ),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender,
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)
        # --8<-- [end:DefaultRequestHandler]

    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
