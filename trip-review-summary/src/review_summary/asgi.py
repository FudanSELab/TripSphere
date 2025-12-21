import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import click
import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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

from starlette.applications import Starlette
from starlette.routing import Mount
from dotenv import load_dotenv

from review_summary.agent.agent import ReviewSummarizerAgent
from review_summary.agent.agent_executor import ReviewSummarizerAgentExecutor
from review_summary.mq.mq import run_mq_consumer


load_dotenv()

# Global variables for MQ task management
mq_task: asyncio.Task | None = None
stop_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: A2AStarletteApplication):
    global mq_task
    logging.info("Starting MQ consumer in background...")
    
    # Start MQ consumer as a background task
    mq_task = asyncio.create_task(run_mq_consumer(stop_event))
    
    yield  # while the ASGI app is running
    
    # Shutdown phase
    logging.info("Shutting down MQ consumer...")
    stop_event.set()  # notify the consumer to exit
    try:
        await asyncio.wait_for(mq_task, timeout=30.0)  # wait up to 10 seconds
    except asyncio.TimeoutError:
        logging.warning("MQ consumer did not shut down gracefully in time")
    logging.info("MQ consumer shutdown complete")

def _create_a2a_app()-> A2AStarletteApplication:
    """Starts the Review Summarizer Agent server."""
    UVICORN_HOST=os.getenv("UVICORN_HOST","0.0.0.0" )
    UVICORN_PORT=int(os.getenv("UVICORN_PORT","9933" ))
    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skill = AgentSkill(
        id='summarize_reviews',
        name='Review Summarization Tool',
        description='Helps with summarizing customer reviews for attractions and businesses',
        tags=['review summarization', 'business reviews', 'attraction reviews'],
        examples=['Summarize the reviews for Eiffel Tower', 'What do people think about Disneyland?', 'Can you provide a summary of reviews for this restaurant?'],
    )
    agent_card = AgentCard(
        name='review_summary',
        description='Analyzes customer reviews and provides concise summaries that answer user questions about businesses and attractions',
        url=f'http://{UVICORN_HOST}:{UVICORN_PORT}',
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
    query_chat_model = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0
    )
    embedding_llm = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )
    request_handler = DefaultRequestHandler(
        agent_executor=ReviewSummarizerAgentExecutor(query_chat_model, embedding_llm),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender= push_sender
    )
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
    return server
    # --8<-- [end:DefaultRequestHandler]

def create_app() -> Starlette:
    inner_app: A2AStarletteApplication = _create_a2a_app()

    app = Starlette(
        lifespan=lifespan,
        routes=[
            Mount("/", app=inner_app),
        ]
    )
    return app

app = create_app()
