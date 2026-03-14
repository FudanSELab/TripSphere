"""Conversational itinerary chat agent.

Replaces the Google ADK deep_agent with a pure LangGraph implementation served
through ag_ui_langgraph.  The graph has a single node that:

  1. Reads the user's current itinerary from the CopilotKit context injected by
     ag_ui_langgraph (populated by the frontend's useCopilotReadable hooks).
  2. Builds a fresh SystemMessage every turn, prepending CHAT_AGENT_INSTRUCTION
     and the itinerary JSON so the LLM always has authoritative context.
  3. Binds the frontend useCopilotAction tools (updateItinerary, addActivity,
     etc.) to ChatOpenAI and invokes the model.

The endpoint is mounted by asgi.py:
    add_langgraph_fastapi_endpoint(app, create_chat_graph(), "/copilotkit")
"""

import json
import logging
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from itinerary_planner.config.settings import get_settings
from itinerary_planner.prompts.chat_agent import CHAT_AGENT_INSTRUCTION

logger = logging.getLogger(__name__)

_SEP = "─" * 60


# ── State ──────────────────────────────────────────────────────────────────

# Use the functional TypedDict form so we can include the 'ag-ui' key
# (hyphen makes it an invalid Python identifier, but a valid dict key).
# ag_ui_langgraph injects:
#   state["tools"]  — list of frontend useCopilotAction tool definitions
#   state["ag-ui"]  — {"tools": [...], "context": [...useCopilotReadable values...]}
# Without these in the schema, get_stream_payload_input() silently drops them
# and the node receives an empty tools list with no readable context.
ChatState = TypedDict(  # type: ignore[misc]
    "ChatState",
    {
        "messages": Annotated[list[AnyMessage], add_messages],
        "tools": list[Any],
        "ag-ui": dict[str, Any],
    },
)


# ── Context extraction helpers ─────────────────────────────────────────────


def _get_readable_desc_and_value(item: Any) -> tuple[str, Any]:
    """Get description and value from a context item (dict or AG-UI Context model)."""
    if isinstance(item, dict):
        return str(item.get("description") or ""), item.get("value")
    return str(getattr(item, "description", None) or ""), getattr(item, "value", None)


def _extract_itinerary_context(
    context_items: list[Any],
) -> tuple[str | None, str | None]:
    """Extract itinerary JSON and destination from AG-UI context items.

    The frontend sends useCopilotReadable as a list of items with
    ``description`` and ``value`` (dict or AG-UI Context model). We prefer the
    item whose description mentions both "itinerary" and "json" (full itinerary);
    otherwise fall back to any item with a value containing "destination".
    """
    fallback_destination: str | None = None
    fallback_json: str | None = None

    for item in context_items:
        desc, value = _get_readable_desc_and_value(item)
        desc_lower = desc.lower()

        # Prefer full itinerary: description contains "itinerary" and "json"
        if "itinerary" in desc_lower and "json" in desc_lower:
            if isinstance(value, dict) and "destination" in value and "day_plans" in value:
                return json.dumps(value, ensure_ascii=False), str(value.get("destination", ""))
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if "destination" in parsed and "day_plans" in parsed:
                        return value, str(parsed.get("destination", ""))
                except (json.JSONDecodeError, ValueError):
                    pass

        # Fallback: any item with destination (e.g. Trip summary readable)
        if value is not None and (fallback_destination is None or fallback_json is None):
            obj: dict[str, Any] | None = None
            if isinstance(value, dict):
                obj = value
            elif isinstance(value, str):
                try:
                    obj = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    obj = None
            if isinstance(obj, dict) and "destination" in obj:
                dest = str(obj.get("destination", ""))
                if dest:
                    fallback_destination = fallback_destination or dest
                if "day_plans" in obj and fallback_json is None:
                    fallback_json = json.dumps(obj, ensure_ascii=False) if isinstance(value, dict) else value

    if fallback_json and fallback_destination:
        return fallback_json, fallback_destination
    if fallback_destination:
        return None, fallback_destination
    return None, None


def _build_system_message(
    itinerary_json: str | None,
    destination: str | None,
    n_context_items: int = 0,
) -> SystemMessage:
    """Return a SystemMessage with CHAT_AGENT_INSTRUCTION and optional itinerary block."""
    content = CHAT_AGENT_INSTRUCTION

    if itinerary_json or destination:
        dest_label = destination or "（见下方 JSON）"
        itinerary_block = (
            f"```json\n{itinerary_json[:6000]}\n```"
            if itinerary_json
            else "（JSON 不可用，仅知目的地）"
        )
        content += (
            f"\n\n## ⚡ 当前用户行程（权威数据，实时注入，绝对优先）\n\n"
            f"**目的地（DESTINATION）: {dest_label}**\n\n"
            f"🚫 严禁为其他城市生成景点或活动。所有输出必须在 **{dest_label}** 范围内。\n\n"
            f"完整行程 JSON：\n\n{itinerary_block}"
        )
        logger.info(
            "[ChatAgent] Injected itinerary context (dest=%s, %d chars)",
            dest_label,
            len(itinerary_json or ""),
        )
    else:
        if n_context_items == 0:
            logger.error(
                "[ChatAgent] No AG-UI context items received. The agent will not know the user's destination."
            )
        else:
            logger.warning(
                "[ChatAgent] Could not extract itinerary/destination from %d context item(s). "
                "The agent may not know the user's destination.",
                n_context_items,
            )

    return SystemMessage(content=content)


# ── Graph factory ──────────────────────────────────────────────────────────


def create_chat_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create and compile the LangGraph conversational chat agent.

    The graph has a single node.  Tool-call loops (LLM calls a frontend action,
    frontend executes it and returns the result, LLM generates the final reply)
    are handled automatically by ag_ui_langgraph between invocations.
    """
    settings = get_settings()
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=settings.openai.api_key,  # type: ignore[arg-type]
        base_url=settings.openai.base_url,
    )

    async def chat_node(
        state: ChatState, config: RunnableConfig
    ) -> dict[str, Any]:
        logger.info(_SEP)
        logger.info("[ChatAgent] Received %d message(s)", len(state["messages"]))

        # ag_ui_langgraph injects frontend useCopilotAction tools into state["tools"]
        # and useCopilotReadable context into state["ag-ui"]["context"].
        # Both keys are declared in ChatState so they survive the schema filter.
        tools: list[Any] = state.get("tools") or []  # type: ignore[misc]
        ag_ui: dict[str, Any] = state.get("ag-ui") or {}  # type: ignore[misc]
        context_items: list[Any] = ag_ui.get("context", [])

        logger.info(
            "[ChatAgent] AG-UI: %d tool(s), %d context item(s)",
            len(tools),
            len(context_items),
        )

        # Build fresh system message with injected itinerary context
        itinerary_json, destination = _extract_itinerary_context(context_items)
        system_msg = _build_system_message(
            itinerary_json, destination, n_context_items=len(context_items)
        )

        # Strip any stale system messages; prepend the freshly built one
        non_system = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        conversation = [system_msg] + non_system

        # Bind frontend useCopilotAction tools and invoke
        llm = model.bind_tools(tools) if tools else model
        response = await llm.ainvoke(conversation, config)

        logger.info(_SEP)
        return {"messages": [response]}

    workflow: StateGraph = StateGraph(ChatState)
    workflow.add_node("chat", chat_node)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)

    # checkpointer required by ag_ui_langgraph for aget_state / thread persistence
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    logger.info("[ChatAgent] Chat graph compiled successfully (with checkpointer)")
    return graph  # type: ignore[return-value]
