"""Deep Agent factory with full context-injection for itinerary modifications.

Root-cause of the "wrong city" bug:
  ag_ui_adk does NOT inject useCopilotReadable values into the LLM request.
  The agent therefore has zero knowledge of the user's itinerary.

Fix strategy (belt + suspenders):
  1. In before_model_callback, read callback_context.state — ag_ui_adk *may*
     populate it with the CopilotKit state (readables).  We log every key so
     we can confirm whether this path works.
  2. If state is empty / does not contain the itinerary, fall back to a
     MongoDB lookup using the user_id available in callback_context.
  3. Whatever we find is appended to the system instruction as authoritative
     context before the LLM is invoked — every single turn.
"""

import json
import logging
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from ag_ui_adk import AGUIToolset

from itinerary_planner.config.settings import get_settings
from itinerary_planner.prompts.deep_agent import DEEP_AGENT_INSTRUCTION
from itinerary_planner.storage.itinerary_repo import ItineraryRepo

logger = logging.getLogger(__name__)

_SEP = "─" * 60


def _ensure_openai_env() -> None:
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url


# ── Text extraction helper ─────────────────────────────────────────────────

def _extract_text(obj: Any) -> str:
    """Best-effort extraction of plain text from ADK message/content objects."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    parts = getattr(obj, "parts", None)
    if parts:
        segments: list[str] = []
        for p in parts:
            if hasattr(p, "text") and p.text:
                segments.append(p.text)
            elif hasattr(p, "function_call") and p.function_call:
                fc = p.function_call
                segments.append(
                    f"[FunctionCall: {getattr(fc, 'name', '?')}({getattr(fc, 'args', '')})]"
                )
            elif hasattr(p, "function_response") and p.function_response:
                fr = p.function_response
                segments.append(
                    f"[FunctionResponse: {getattr(fr, 'name', '?')} "
                    f"→ {str(getattr(fr, 'response', ''))[:100]}]"
                )
        return " ".join(segments)
    return str(obj)


# ── Module-level simple callbacks (logging only, no repo needed) ───────────

def _after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    text = _extract_text(llm_response)
    logger.info("[DeepAgent] ◀ LLM RESPONSE: %s", text[:400].replace("\n", " ↵ "))
    return None


def _before_tool_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict | None:
    logger.info(_SEP)
    logger.info("[DeepAgent] 🔧 TOOL CALL  → %s", tool.name)
    for k, v in args.items():
        v_str = str(v)
        logger.info(
            "[DeepAgent]   arg %-20s = %s",
            k,
            v_str[:300] if len(v_str) > 300 else v_str,
        )
    logger.info(_SEP)
    return None


def _after_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    logger.info(
        "[DeepAgent] ✅ TOOL RESULT ← %s  →  %s",
        tool.name,
        str(tool_response)[:300],
    )
    return None


# ── Factory ────────────────────────────────────────────────────────────────

def create_deep_agent(
    model: str = "openai/gpt-4o-mini",
    repo: ItineraryRepo | None = None,
) -> LlmAgent:
    """Create the Deep Agent with guaranteed itinerary context injection.

    ``repo`` is optional but strongly recommended — when provided, the
    before_model_callback can fall back to a MongoDB lookup to ensure the
    agent always sees the current itinerary even if ag_ui_adk doesn't inject
    the CopilotKit state.
    """
    _ensure_openai_env()

    async def _before_model_callback(  # noqa: C901  (complex by necessity)
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        logger.info(_SEP)
        logger.info("[DeepAgent] ▶ LLM REQUEST  model=%s", llm_request.model)

        # ── Step 1: Inspect session state (ag_ui_adk may put readables here) ──
        state = callback_context.state
        state_dict: dict[str, Any] = {}
        try:
            # ADK State is dict-like; convert safely
            if hasattr(state, "to_dict"):
                state_dict = state.to_dict()
            elif hasattr(state, "keys"):
                state_dict = {k: state[k] for k in state.keys()}
            elif isinstance(state, dict):
                state_dict = state
        except Exception as exc:
            logger.warning("[DeepAgent] Could not read state: %s", exc)

        logger.info(
            "[DeepAgent] Session state — %d key(s): %s",
            len(state_dict),
            list(state_dict.keys())[:15],
        )

        itinerary_json: str | None = None
        destination: str | None = None

        for key, value in state_dict.items():
            key_s = str(key).lower()
            val_preview = str(value)[:120]
            logger.info("[DeepAgent]   state[%r] = %s", key, val_preview)

            # CopilotKit readables arrive with their description as key
            if ("itinerary" in key_s or "travel" in key_s) and "json" in key_s:
                try:
                    itinerary_json = (
                        json.dumps(value, ensure_ascii=False)
                        if not isinstance(value, str)
                        else value
                    )
                    if isinstance(value, dict):
                        destination = value.get("destination")
                    logger.info(
                        "[DeepAgent] ✔ Found itinerary JSON in state (key=%r, dest=%s)",
                        key,
                        destination,
                    )
                except Exception as exc:
                    logger.warning("[DeepAgent] Failed to serialize state itinerary: %s", exc)

            elif "summary" in key_s or "destination" in key_s or "trip" in key_s:
                if isinstance(value, dict) and "destination" in value and not destination:
                    destination = value["destination"]
                    logger.info("[DeepAgent] ✔ Found destination in state summary: %s", destination)

        # ── Step 2: Fallback — MongoDB lookup by user_id ──────────────────────
        if itinerary_json is None and repo is not None:
            uid: str = str(getattr(callback_context, "user_id", "") or "").strip()
            logger.info("[DeepAgent] callback_context.user_id = %r", uid)

            if uid:
                try:
                    docs = await repo.list_by_user(user_id=uid, limit=1)
                    if docs:
                        doc = await repo.get_any(itinerary_id=str(docs[0]["_id"]))
                        if doc and doc.get("itinerary"):
                            itinerary_json = json.dumps(
                                doc["itinerary"], ensure_ascii=False
                            )
                            destination = doc.get("destination", destination)
                            logger.info(
                                "[DeepAgent] ✔ MongoDB fallback succeeded: %s (user=%s)",
                                destination,
                                uid,
                            )
                        else:
                            logger.warning(
                                "[DeepAgent] MongoDB doc found but has no itinerary"
                            )
                    else:
                        logger.warning(
                            "[DeepAgent] No itineraries in MongoDB for user_id=%r", uid
                        )
                except Exception as exc:
                    logger.error("[DeepAgent] MongoDB lookup failed: %s", exc)
            else:
                logger.warning(
                    "[DeepAgent] user_id is empty — cannot do MongoDB lookup"
                )

        # ── Step 3: Inject into system instruction ────────────────────────────
        if itinerary_json or destination:
            if llm_request.config is None:
                # Shouldn't normally happen, but guard anyway
                logger.warning("[DeepAgent] llm_request.config is None, skipping inject")
            else:
                existing_sys = (
                    _extract_text(llm_request.config.system_instruction)
                    if llm_request.config.system_instruction
                    else DEEP_AGENT_INSTRUCTION
                )
                dest_label = destination or "（见下方 JSON）"
                itinerary_block = (
                    f"```json\n{itinerary_json[:6000]}\n```"
                    if itinerary_json
                    else "（JSON 不可用，仅知目的地）"
                )
                injection = (
                    f"\n\n"
                    f"## ⚡ 当前用户行程（权威数据，实时注入，绝对优先）\n\n"
                    f"**目的地（DESTINATION）: {dest_label}**\n\n"
                    f"🚫 严禁为其他城市生成景点或活动。所有输出必须在 **{dest_label}** 范围内。\n\n"
                    f"完整行程 JSON：\n\n"
                    f"{itinerary_block}"
                )
                llm_request.config.system_instruction = existing_sys + injection
                logger.info(
                    "[DeepAgent] ✅ Injected itinerary context for '%s' "
                    "(%d itinerary chars, %d total sys chars)",
                    dest_label,
                    len(itinerary_json or ""),
                    len(existing_sys + injection),
                )
        else:
            logger.error(
                "[DeepAgent] ❌ NO ITINERARY CONTEXT AVAILABLE — "
                "agent will not know the destination! "
                "Check that: (1) ag_ui_adk injects state, OR "
                "(2) repo is passed and user_id is non-empty."
            )

        # ── Step 4: Log the final system instruction and conversation ─────────
        if llm_request.config and llm_request.config.system_instruction:
            sys_text = _extract_text(llm_request.config.system_instruction)
            logger.info(
                "[DeepAgent] SYSTEM INSTRUCTION (%d chars):\n%s",
                len(sys_text),
                sys_text[:2000],
            )
            if len(sys_text) > 2000:
                logger.info("[DeepAgent] ... (system instruction truncated)")
        else:
            logger.warning("[DeepAgent] ⚠ No system instruction in request!")

        contents = llm_request.contents or []
        logger.info("[DeepAgent] CONVERSATION (%d messages):", len(contents))
        for i, content in enumerate(contents):
            role = getattr(content, "role", "?")
            text = _extract_text(content)
            logger.info(
                "[DeepAgent]   [%d] role=%-12s | %s",
                i,
                role,
                text[:300].replace("\n", " ↵ "),
            )

        logger.info(_SEP)
        return None  # continue normal LLM invocation

    agent = LlmAgent(
        name="itinerary_deep_agent",
        model=LiteLlm(model=model),
        instruction=DEEP_AGENT_INSTRUCTION,
        tools=[AGUIToolset()],
        before_model_callback=_before_model_callback,
        after_model_callback=_after_model_callback,
        before_tool_callback=_before_tool_callback,
        after_tool_callback=_after_tool_callback,
    )

    logger.info(
        "Deep Agent created: %s (model=%s, repo=%s)",
        agent.name,
        model,
        "attached" if repo else "none",
    )
    return agent
