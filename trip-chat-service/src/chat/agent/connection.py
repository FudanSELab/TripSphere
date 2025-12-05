from typing import Callable

from a2a.client import Client, ClientFactory
from a2a.types import (
    AgentCard,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)
from a2a.types import Message as A2AMessage
from a2a.types import Task as A2ATask
from a2a.types import TaskState as A2ATaskState

TaskCallbackArg = A2ATask | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], A2ATask]


class RemoteAgentConnection:
    def __init__(self, agent_card: AgentCard, client_factory: ClientFactory) -> None:
        self.agent_card = agent_card
        self.agent_client: Client = client_factory.create(agent_card)

    async def send_message(self, message: A2AMessage) -> A2ATask | A2AMessage:
        received_task: A2ATask | None = None
        async for event in self.agent_client.send_message(message):
            if isinstance(event, A2AMessage):
                return event
            if self.is_terminal_or_interrupted(event[0]):
                return event[0]
            received_task, _ = event

        if received_task is None:
            raise RuntimeError("No Task or Message received from agent.")
        return received_task

    def is_terminal_or_interrupted(self, task: A2ATask) -> bool:
        return task.status.state in [
            A2ATaskState.completed,
            A2ATaskState.canceled,
            A2ATaskState.failed,
            A2ATaskState.input_required,
            A2ATaskState.unknown,
        ]
