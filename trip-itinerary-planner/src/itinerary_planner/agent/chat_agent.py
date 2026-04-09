"""Conversational itinerary chat agent — ReAct edition.

Architecture
────────────
A custom 2-node LangGraph (agent → tools → agent → …) served through
ag_ui_langgraph.  The itinerary is held in the graph state so the
frontend can sync it bidirectionally via CopilotKit's useCoAgent hook:

  frontend state.itinerary  ←→  ChatState["itinerary"]

Flow per user turn
──────────────────
1. CopilotKit sends the current agent state (incl. itinerary) in
   RunAgentInput.state — ag_ui_langgraph merges it into the graph state.
2. agent_node builds a fresh SystemMessage from state["itinerary"],
   strips stale system messages, binds tools, and calls the LLM.
3. If the LLM emits tool calls, ToolNode executes them.
   Every tool updates state["itinerary"] (and/or "markdown_content")
   atomically via a Command return + ToolMessage.
4. After the last tool call the LLM generates a text reply.
5. ag_ui_langgraph emits StateSnapshotEvent → CopilotKit → useCoAgent
   updates state.itinerary on the frontend in real-time.
"""

import json
import logging
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from itinerary_planner.config.settings import get_settings
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.prompts.chat_agent import CHAT_AGENT_INSTRUCTION
from itinerary_planner.tools import (
    INLINE_TOOLS,
    geocoding_tool,
    make_regenerate_day_tool,
)

logger = logging.getLogger(__name__)

_SEP = "─" * 60


# ── State ──────────────────────────────────────────────────────────────────

ChatState = TypedDict(
    "ChatState",
    {
        # Full conversation history; add_messages merges instead of replacing.
        "messages": Annotated[list[AnyMessage], add_messages],
        # Current itinerary as a plain dict (JSON-serialisable).
        # Initialised by the frontend via useCoAgent initialState / setState.
        # Tools update it via Command; ag_ui_langgraph streams it back via
        # StateSnapshotEvent so the frontend ItineraryViewer re-renders live.
        "itinerary": dict[str, Any] | None,
        # Markdown narrative synced alongside the itinerary.
        "markdown_content": str,
    },
)


# ── System prompt builder ──────────────────────────────────────────────────


def _build_system_message(itinerary: dict[str, Any] | None) -> SystemMessage:
    """Return a SystemMessage embedding the current itinerary JSON."""
    content = CHAT_AGENT_INSTRUCTION

    if itinerary:
        dest = itinerary.get("destination", "（未知）")
        itinerary_json = json.dumps(itinerary, ensure_ascii=False)[:6000]
        content += (
            f"\n\n## ⚡ 当前用户行程（权威数据，实时注入，绝对优先）\n\n"
            f"**目的地（DESTINATION）: {dest}**\n\n"
            f"🚫 严禁为其他城市生成景点或活动。所有输出必须在 **{dest}** 范围内。\n\n"
            f"完整行程 JSON：\n\n```json\n{itinerary_json}\n```"
        )
        logger.info(
            "[ChatAgent] System prompt: dest=%s, itinerary %d chars",
            dest,
            len(itinerary_json),
        )
    else:
        logger.warning(
            "[ChatAgent] No itinerary in state; agent has no destination context."
        )

    return SystemMessage(content=content)


# ── Graph factory ──────────────────────────────────────────────────────────


def create_chat_graph(nacos_naming: NacosNaming | None = None) -> CompiledStateGraph:  # type: ignore[type-arg]
    """Build and compile the ReAct chat graph.

    Parameters
    ----------
    nacos_naming:
        When provided, the ``regenerate_day`` tool is included; it uses
        Nacos to discover the attraction service for fresh coordinates.
    """
    settings = get_settings()
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=settings.openai.api_key,
        base_url=settings.openai.base_url,
    )

    all_tools = [geocoding_tool, *INLINE_TOOLS]
    if nacos_naming is not None:
        all_tools.append(make_regenerate_day_tool(nacos_naming))

    tool_node = ToolNode(all_tools)
    model_with_tools = model.bind_tools(all_tools)

    # ── Nodes ──────────────────────────────────────────────────────────────

    async def agent_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        logger.info(_SEP)
        logger.info(
            "[ChatAgent] messages=%d  itinerary=%s",
            len(state["messages"]),
            "present" if state.get("itinerary") else "absent",
        )

        system_msg = _build_system_message(state.get("itinerary"))

        # Strip any stale system messages from prior turns
        non_system = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        conversation = [system_msg, *non_system]

        response = await model_with_tools.ainvoke(conversation, config)
        logger.info(_SEP)
        return {"messages": [response]}

    def should_continue(state: ChatState) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return "__end__"

    # ── Graph ──────────────────────────────────────────────────────────────

    workflow: StateGraph[ChatState] = StateGraph(ChatState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "__end__": END},
    )
    workflow.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    logger.info(
        "[ChatAgent] ReAct graph compiled (%d tool(s), checkpointer=MemorySaver)",
        len(all_tools),
    )
    return graph
