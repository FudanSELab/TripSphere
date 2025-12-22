import os
from collections.abc import AsyncIterable
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool  # pyright: ignore[reportUnknownVariableType]
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.graph.message import (  # pyright: ignore[reportMissingTypeStubs]
    add_messages,
)
from langgraph.graph.state import (  # pyright: ignore[reportMissingTypeStubs]
    CompiledStateGraph,
)
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from pymongo import AsyncMongoClient

import review_summary.agent.grpc.attraction as attraction_grpc
from review_summary.config.settings import get_settings
from review_summary.index.embedding import text_to_embedding_async
from review_summary.index.repository import ReviewEmbeddingRepository
from review_summary.prompt.agent import FORMAT_INSTRUCTION, SYSTEM_INSTRUCTION

# Load environment variables
ATTRACTION_GRPC_SERVICE_HOST = os.getenv("ATTRACTION_GRPC_SERVICE_HOST", "127.0.0.1")
ATTRACTION_GRPC_SERVICE_PORT = int(os.getenv("ATTRACTION_GRPC_SERVICE_PORT", "9007"))

# Initialize MongoDB client and repository
settings = get_settings()
client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
db = client[settings.mongo.database]
repo = ReviewEmbeddingRepository(db[ReviewEmbeddingRepository.COLLECTION_NAME])


class ResponseFormat(BaseModel):
    """Generate a structured response based on retrieved reviews.
    - Use status='completed' when you can answer the user's question (even if reviews are empty).
    - Use status='input_required' only if the user didn't specify an attraction name or query clearly.
    - Use status='error' only for tool failures.
    - The 'message' field must always contain a user-facing response in Chinese.
    """

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    structured_response: ResponseFormat | None


@tool
async def get_attraction_id(attraction_name: str) -> str:
    """Get the ID of an attraction based on its name.

    Args:
        attraction_name: Name of the attraction to get the ID for.

    Returns:
        A dictionary containing the attraction ID, or an error message if
        the request fails.
    """
    return await attraction_grpc.find_attraction_id_by_name(attraction_name)


@tool
async def get_reviews(
    attraction_id: str, max_reviews: int = 20, query: str = ""
) -> dict[str, Any]:
    """Use this to get reviews for a business.

    Args:
        attraction_id: The ID of the attraction to get reviews for.
        max_reviews: Maximum number of reviews to retrieve. Defaults to 20.
        query: The query text to find similar reviews.

    Returns:
        A dictionary containing the reviews data, or an error message if
        the request fails.
    """
    # Get the embedding vector for the query
    query_embedding = await text_to_embedding_async(query)

    # Retrieve all review embeddings for the attraction from the database
    result = await repo.find_by_attraction_id(attraction_id=attraction_id)

    # If no embeddings are found, return an empty list
    if not result:
        return {"reviews": []}

    # Compute cosine similarity between each review embedding and the query embedding
    similarities: list[tuple[float, str]] = []
    for record in result:
        stored_embedding = record.embedding
        # Compute dot product
        dot_product = sum(q * s for q, s in zip(query_embedding, stored_embedding))
        # Compute vector norms
        query_norm = sum(q * q for q in query_embedding) ** 0.5
        stored_norm = sum(s * s for s in stored_embedding) ** 0.5
        # Compute cosine similarity
        if query_norm == 0 or stored_norm == 0:
            similarity = 0
        else:
            similarity = dot_product / (query_norm * stored_norm)
        # Append to similarities list, using review_content
        similarities.append((similarity, record.review_content))

    # Sort by cosine similarity and take top max_reviews
    similarities.sort(reverse=True, key=lambda x: x[0])
    top_reviews = [review for _, review in similarities[:max_reviews]]

    return {"reviews": top_reviews}


class ReviewSummarizerAgent:
    """ReviewSummarizerAgent - a specialized assistant for summarizing business reviews."""

    def __init__(self, chat_model: ChatOpenAI, embedding_model: OpenAIEmbeddings):
        self.model = chat_model
        self.tools = [get_attraction_id, get_reviews]
        self.embedding_model = embedding_model

        # Create the graph
        self.graph = self._create_graph()

    def _create_graph(
        self,
    ) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
        # Create state graph
        workflow = StateGraph[AgentState, None, AgentState, AgentState](AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)  # pyright: ignore[reportUnknownMemberType]
        workflow.add_node("tools", ToolNode(self.tools))  # pyright: ignore[reportUnknownMemberType]

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent", self._should_call_tool, {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")

        # Set finish point
        workflow.set_finish_point("agent")

        return workflow.compile(checkpointer=MemorySaver())  # pyright: ignore[reportUnknownMemberType]

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        messages = state["messages"]
        print(f"Model called with messages: {messages}")
        last_msg = state["messages"][-1]
        if (isinstance(last_msg, ToolMessage) and len(state["messages"]) == 4) or (
            len(state["messages"]) == 2 and isinstance(last_msg, HumanMessage)
        ):
            model_runnable = self.model.bind_tools(self.tools)  # pyright: ignore[reportUnknownMemberType]
            response = model_runnable.invoke(messages)
            return {"messages": [response]}
        else:
            full_messages = messages + [SystemMessage(content=FORMAT_INSTRUCTION)]
            model_runnable = self.model.with_structured_output(ResponseFormat)  # type: ignore
            structured_response = model_runnable.invoke(full_messages)  # pyright: ignore[reportUnknownVariableType]
            return {"structured_response": structured_response}

    def _should_call_tool(self, state: AgentState) -> str:
        # Check if the last message has tool calls
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            return "continue"
        return "end"

    async def stream(
        self, query: str, context_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        inputs = {
            "messages": [
                SystemMessage(content=SYSTEM_INSTRUCTION),
                HumanMessage(content=query),
            ]
        }
        config = RunnableConfig({"configurable": {"thread_id": context_id}})

        # Stream the execution
        final_state = None
        async for event in self.graph.astream(inputs, config, stream_mode="values"):  # type: ignore
            if "messages" in event and event["messages"]:
                last_message = event["messages"][-1]

                if isinstance(last_message, AIMessage) and last_message.tool_calls:
                    # Check which tool is being called to provide appropriate feedback
                    tool_names = [tc.get("name", "") for tc in last_message.tool_calls]
                    if "get_attraction_id" in tool_names:
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": "Looking up attraction ID...",
                        }
                    elif "get_reviews" in tool_names:
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": "Retrieving reviews for analysis...",
                        }
                elif isinstance(last_message, ToolMessage):
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": "Analyzing the reviews..",
                    }
            final_state = event

        # Get response from final state
        if final_state and "structured_response" in final_state:
            response = final_state["structured_response"]
            if response.status == "completed":
                yield {
                    "content": response.message,
                    "is_task_complete": True,
                    "require_user_input": False,
                }
            elif response.status == "input_required":
                yield {
                    "content": response.message,
                    "is_task_complete": False,
                    "require_user_input": True,
                }
            else:  # error
                yield {
                    "content": response.message,
                    "is_task_complete": False,
                    "require_user_input": False,
                }
        else:
            yield {
                "content": "We are unable to process your request at the moment."
                " Please try again.",
                "is_task_complete": False,
                "require_user_input": False,
            }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
