import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

logger = logging.getLogger(__name__)


class A2aAgentExecutor(AgentExecutor):
    def __init__(self) -> None: ...

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError
