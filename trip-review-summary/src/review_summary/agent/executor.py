import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient

logger = logging.getLogger(__name__)


class ReviewSummaryAgentExecutor(AgentExecutor):
    def __init__(
        self, neo4j_driver: AsyncDriver, qdrant_client: AsyncQdrantClient
    ) -> None:
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError
