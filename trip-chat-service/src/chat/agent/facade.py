import asyncio
import json
import logging
from base64 import b64decode
from dataclasses import dataclass, field
from mimetypes import guess_type
from typing import Any, AsyncGenerator, Self

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import AgentCard, FileWithUri, Role, TransportProtocol
from a2a.types import DataPart as A2ADataPart
from a2a.types import Message as A2AMessage
from a2a.types import Part as A2APart
from a2a.types import TaskState as A2ATaskStete
from a2a.types import TextPart as A2ATextPart
from httpx import AsyncClient
from pydantic_ai import Agent, BinaryContent, ModelSettings, RunContext, Tool
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from chat.agent.connection import RemoteAgentConnection, TaskUpdateCallback
from chat.agent.context import ContextProvider, convert_message
from chat.common.parts import Part
from chat.config.settings import get_settings
from chat.conversation.models import Author, Conversation, Message
from chat.infra.nacos.naming import NacosNaming
from chat.prompts.agent import DELEGATOR_INSTRUCTIONS
from chat.task.models import Task

logger = logging.getLogger(__name__)


@dataclass
class FacadeDeps:
    conversation_id: str
    task_id: str | None
    user_query_id: str
    active_agent: str | None = field(default=None)
    session_active: bool = field(default=False)


class AgentFacade:
    """
    The orchestrator for scheduling agents and delegating tasks.
    """

    def __init__(
        self,
        httpx_client: AsyncClient,
        context_provider: ContextProvider | None = None,
        task_callback: TaskUpdateCallback | None = None,
    ) -> None:
        self.task_callback = task_callback
        self.httpx_client = httpx_client
        config = ClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.client_factory = ClientFactory(config)
        self.remote_agent_connections: dict[str, RemoteAgentConnection] = {}
        self.agent_cards: dict[str, AgentCard] = {}
        self.context_provider = context_provider
        self.root_agent: Agent[FacadeDeps] | None = None

    async def _post_init(self, remote_agent_urls: list[str]) -> None:
        async with asyncio.TaskGroup() as group:
            for base_url in remote_agent_urls:
                group.create_task(self.register_remote_agent(base_url))

        openai_settings = get_settings().openai
        chat_model = OpenAIChatModel(
            model_name="gpt-4o-mini",  # TODO: Make configurable
            provider=OpenAIProvider(
                base_url=openai_settings.base_url,
                api_key=openai_settings.api_key.get_secret_value(),
            ),
            settings=ModelSettings(temperature=0.0),
        )

        self.root_agent = Agent[FacadeDeps](
            model=chat_model,
            instructions=self.root_instruction,
            deps_type=FacadeDeps,
            tools=[Tool(self.send_message, takes_ctx=True)],
            instrument=True,
        )

    async def register_remote_agent(self, base_url: str) -> None:
        card_resolver = A2ACardResolver(self.httpx_client, base_url)
        agent_card = await card_resolver.get_agent_card()
        remote_connection = RemoteAgentConnection(agent_card, self.client_factory)
        self.remote_agent_connections[agent_card.name] = remote_connection
        self.agent_cards[agent_card.name] = agent_card

    @classmethod
    async def create_facade(
        cls,
        httpx_client: AsyncClient,
        _: NacosNaming,
        context_provider: ContextProvider | None = None,
    ) -> Self:
        instance = cls(httpx_client, context_provider=context_provider)
        # TODO: Remote agents discovery through Nacos
        await instance._post_init(["http://localhost:8000"])
        # await instance._post_init(remote_agent_urls=[])
        return instance

    async def invoke(
        self,
        conversation: Conversation,
        user_query: Message,
        associated_task: Task | None = None,
    ) -> Message:
        if self.root_agent is None:
            raise RuntimeError("Root agent is not initialized.")

        message_history: list[ModelMessage] = []
        if self.context_provider is not None:
            messages = await self.context_provider.history_messages(exclude_last=True)
            message_history = [convert_message(message) for message in messages]

        result = await self.root_agent.run(
            user_query.text_content(),
            message_history=message_history,
            deps=FacadeDeps(
                conversation_id=conversation.conversation_id,
                task_id=associated_task.task_id if associated_task else None,
                user_query_id=user_query.message_id,
                active_agent=associated_task.task_agent if associated_task else None,
                session_active=(
                    (not associated_task.is_terminal()) if associated_task else False
                ),
            ),
        )
        logger.debug(f"Root agent run result: {result.output}")
        return Message(
            conversation_id=conversation.conversation_id,
            author=Author.agent(),
            content=[Part.from_text(result.output)],
        )

    async def stream(
        self,
        conversation: Conversation,
        user_query: Message,
        associated_task: Task | None = None,
    ) -> AsyncGenerator[Any, None]:  # TODO: Specify proper type
        if self.root_agent is None:
            raise RuntimeError("Root agent is not initialized.")

        yield ""  # TODO

    def remote_agents(self) -> list[dict[str, str]]:
        if not self.agent_cards:
            return []  # No remote agents available

        remote_agents_info: list[dict[str, str]] = []
        for card in self.agent_cards.values():
            logger.debug(f"Found registered agent: {card.name}")
            agent_info = {"name": card.name, "description": card.description}
            remote_agents_info.append(agent_info)
        return remote_agents_info

    def root_instruction(self, ctx: RunContext[FacadeDeps]) -> str:
        remote_agents_info = self.remote_agents()
        agents_info = [json.dumps(agent) for agent in remote_agents_info]
        agents = "\n".join(agents_info)
        current_active_agent: str | None = None
        if ctx.deps.session_active and ctx.deps.active_agent:
            current_active_agent = ctx.deps.active_agent
        return DELEGATOR_INSTRUCTIONS.format(
            agents=agents, current_active_agent=current_active_agent
        )

    async def send_message(
        self, ctx: RunContext[FacadeDeps], agent_name: str, message: str
    ) -> list[str | dict[str, Any] | BinaryContent]:
        """
        Sends a message to a remote agent named `agent_name`.

        Arguments:
            agent_name: Name of the remote agent to which the message are sent.
            message: The message to send to the agent for the task.

        Returns:
            A list of response parts from the remote agent.
        """
        logger.debug(f"Sending message to agent {agent_name}: {message}")
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} is not found.")

        ctx.deps.active_agent = agent_name
        connection = self.remote_agent_connections[agent_name]

        if not connection:
            raise ValueError(f"Connection is not available for {agent_name}.")

        task_id = ctx.deps.task_id
        context_id = ctx.deps.conversation_id
        message_id = ctx.deps.user_query_id
        request_message: A2AMessage = A2AMessage(
            context_id=context_id,
            message_id=message_id,
            parts=[A2APart(root=A2ATextPart(text=message))],
            role=Role.user,
            task_id=task_id,
        )

        result = await connection.send_message(request_message)
        if isinstance(result, A2AMessage):
            logger.debug(f"Received A2AMessage from agent {agent_name}: {result}")
            return [convert_part(part) for part in result.parts]

        logger.debug(f"Received A2ATask from agent {agent_name}: {result}")
        # Assume completion unless a state returns that isn't complete
        ctx.deps.session_active = result.status.state not in [
            A2ATaskStete.completed,
            A2ATaskStete.canceled,
            A2ATaskStete.failed,
            A2ATaskStete.unknown,
        ]
        if ctx.deps.task_id is None:
            ctx.deps.task_id = result.id

        if result.status.state == A2ATaskStete.input_required:
            ...  # TODO: Handle input required state
        elif result.status.state == A2ATaskStete.canceled:
            raise RuntimeError(f"Agent {agent_name} task {result.id} was cancelled.")
        elif result.status.state == A2ATaskStete.failed:
            raise RuntimeError(f"Agent {agent_name} task {result.id} failed.")

        response: list[str | dict[str, Any] | BinaryContent] = []
        if result.status.message:
            # Assume the information is in the A2AMessage of A2ATaskStatus
            response.extend(convert_part(part) for part in result.status.message.parts)
        if result.artifacts is not None:
            for artifact in result.artifacts:
                response.extend(convert_part(part) for part in artifact.parts)
        return response


def convert_part(part: A2APart) -> str | dict[str, Any] | BinaryContent:
    """
    Convert an A2A Part to a format suitable for PydanticAI.
    """
    if isinstance(part.root, A2ATextPart):
        return part.root.text

    if isinstance(part.root, A2ADataPart):
        return part.root.data

    file = part.root.file
    if isinstance(file, FileWithUri):
        return file.model_dump()

    media_type: str | None = None
    if file.mime_type is not None:
        media_type = file.mime_type
    elif file.name is not None:
        media_type, _ = guess_type(file.name)
    return BinaryContent(
        data=b64decode(file.bytes),
        media_type=media_type or "application/octet-stream",
        identifier=file.name,
    )
