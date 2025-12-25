import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

from review_summary.agent.agent import ReviewSummaryAgent

logger = logging.getLogger(__name__)


class ReviewSummaryAgentExecutor(AgentExecutor):
    def __init__(self, agent: ReviewSummaryAgent) -> None:
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError
