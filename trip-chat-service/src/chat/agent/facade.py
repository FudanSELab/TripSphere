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
from a2a.types import Task as A2ATask
from a2a.types import TaskState as A2ATaskStete
from a2a.types import TextPart as A2ATextPart
from httpx import AsyncClient
from pydantic_ai import Agent, BinaryContent, ModelSettings, RunContext, Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from chat.agent.connection import RemoteAgentConnection, TaskUpdateCallback
from chat.agent.context import ContextProvider
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
        self.context_provider: ContextProvider | None = None
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
        )

    async def register_remote_agent(self, base_url: str) -> None:
        card_resolver = A2ACardResolver(self.httpx_client, base_url)
        agent_card = await card_resolver.get_agent_card()
        remote_connection = RemoteAgentConnection(agent_card, self.client_factory)
        self.remote_agent_connections[agent_card.name] = remote_connection
        self.agent_cards[agent_card.name] = agent_card

    @classmethod
    async def create_facade(
        cls, httpx_client: AsyncClient, nacos_naming: NacosNaming
    ) -> Self:
        instance = cls(httpx_client)
        # TODO: Remote agents discovery through Nacos
        # await instance._post_init(["http://localhost:8001"])
        await instance._post_init([])
        return instance

    async def invoke(
        self,
        conversation: Conversation,
        user_query: Message,
        associated_task: Task | None = None,
    ) -> Message:
        if self.root_agent is None:
            raise RuntimeError("Root agent is not initialized.")

        # TODO: Implement context injection
        result = await self.root_agent.run(
            user_query.text_content(),
            deps=FacadeDeps(
                conversation_id=conversation.conversation_id,
                task_id=associated_task.task_id if associated_task else None,
                user_query_id=user_query.message_id,
            ),
        )
        logger.debug(f"Root agent run result: {result}")
        return Message(
            conversation_id=conversation.conversation_id, author=Author.agent()
        )  # TODO: Dummy return

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
            logger.debug(f"Found agent card: {card}")
            remote_agents_info.append(
                {"name": card.name, "description": card.description}
            )
        return remote_agents_info

    def root_instruction(self, ctx: RunContext[FacadeDeps]) -> str:
        remote_agents_info = self.remote_agents()
        agents_info = [json.dumps(agent) for agent in remote_agents_info]
        agents = "\n".join(agents_info)
        return DELEGATOR_INSTRUCTIONS.format(
            agents=agents, current_active_agent=ctx.deps.active_agent
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

        response = await connection.send_message(request_message)
        if isinstance(response, A2AMessage):
            return convert_parts(response.parts)
        task: A2ATask = response
        # Assume completion unless a state returns that isn't complete
        ctx.deps.session_active = task.status.state not in [
            A2ATaskStete.completed,
            A2ATaskStete.canceled,
            A2ATaskStete.failed,
            A2ATaskStete.unknown,
        ]
        ctx.deps.task_id = task.id

        raise NotImplementedError


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


def convert_parts(parts: list[A2APart]) -> list[str | dict[str, Any] | BinaryContent]:
    """
    Convert a list of A2A Parts to formats suitable for PydanticAI.
    """
    return [convert_part(part) for part in parts]
