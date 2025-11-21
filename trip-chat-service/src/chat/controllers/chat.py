from litestar import Controller, post
from litestar.di import Provide
from pydantic import BaseModel, Field

from chat.assistant.agent import ChatAssistant
from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
)
from chat.common.schema import ResponseBody
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import ConversationRepository


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="UUID of the conversation.")
    query: str = Field(..., description="User's chat query message.")


class ChatResponse(BaseModel):
    query_id: str = Field(..., description="UUID of the user query message.")
    answer_id: str = Field(..., description="UUID of the chat answer message.")
    task_id: str | None = Field(
        default=None, description="Optional UUID of the associated task."
    )


class ChatController(Controller):
    path = "/chat"
    tags = ["Chat"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "message_repository": Provide(provide_message_repository),
        "conversation_manager": Provide(provide_conversation_manager),
    }

    @post()
    async def chat(
        self,
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager,
        data: ChatRequest,
    ) -> ResponseBody[ChatResponse]:
        conversation = await conversation_repository.find_by_id(data.conversation_id)
        if conversation is None:
            raise Exception  # TODO: Use proper exception

        query_message = await conversation_manager.append_text_query(
            conversation=conversation, query=data.query
        )
        assistant = ChatAssistant(model_name="gpt-4o-mini")
        state = await assistant.run(query_message)
        agent_answer = await conversation_manager.append_agent_answer(
            conversation=conversation,
            author=state.author,
            answer_parts=state.response,
            task_id=state.task.task_id if state.task else None,
        )
        # TODO: Handle task creation and association
        return ResponseBody(
            data=ChatResponse(
                query_id=query_message.message_id,
                answer_id=agent_answer.message_id,
                task_id=agent_answer.task_id,
            )
        )
