import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

ReviewTargetType = Literal["hotel", "attraction"]


@dataclass(frozen=True, slots=True)
class ReviewTarget:
    target_id: str
    target_type: ReviewTargetType


def extract_review_target(
    state: Mapping[str, Any] | None,
) -> ReviewTarget | None:
    if state is None:
        return None

    raw_contexts = state.get("_ag_ui_context")
    if not isinstance(raw_contexts, list):
        return None

    targets: set[ReviewTarget] = set()
    for raw_context in raw_contexts:
        if not isinstance(raw_context, Mapping):
            continue
        if raw_context.get("description") != "review target context":
            continue

        target = _parse_review_target_value(raw_context.get("value"))
        if target is None:
            return None
        targets.add(target)

    if len(targets) != 1:
        return None
    return next(iter(targets))


def _parse_review_target_value(value: Any) -> ReviewTarget | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, Mapping):
        return None

    raw_target_id = value.get("targetId")
    raw_target_type = value.get("targetType")
    if not isinstance(raw_target_id, str) or not raw_target_id.strip():
        return None
    if not isinstance(raw_target_type, str):
        return None

    normalized_target_type = raw_target_type.strip().lower()
    if normalized_target_type == "hotel":
        target_type: ReviewTargetType = "hotel"
    elif normalized_target_type == "attraction":
        target_type = "attraction"
    else:
        return None
    return ReviewTarget(
        target_id=raw_target_id.strip(),
        target_type=target_type,
    )


class HotelViewingToolset(BaseToolset):
    def __init__(self, tool_name_prefix: str = "hotel_viewing") -> None:
        super().__init__(tool_name_prefix=tool_name_prefix)
        self._get_hotel = FunctionTool(self.get_hotel)
        self._get_room_types = FunctionTool(self.get_room_types)

    def get_hotel(self, tool_context: ToolContext) -> dict[str, Any]:
        """Get the hotel information that the user is viewing.

        Returns:
            dict[str, Any]: A dictionary with the hotel information, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        ag_ui_context: list[dict[str, Any]] = (
            tool_context.state.get("_ag_ui_context") or []
        )
        logger.debug("ag_ui_context: %s", ag_ui_context)
        for ctx in ag_ui_context:
            if ctx.get("description") == "hotel context":
                hotel_context = ctx.get("value")
                if hotel_context:
                    return {
                        "status": "success",
                        "message": "The hotel information is included in the result.",
                        "result": json.loads(hotel_context)["hotel"],
                    }
        return {
            "status": "error",
            "message": "No hotel context found",
            "result": None,
        }

    def get_room_types(self, tool_context: ToolContext) -> dict[str, Any]:
        """Get the room types of the hotel that the user is viewing.

        Returns:
            dict[str, Any]: A dictionary with the room types information, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        ag_ui_context: list[dict[str, Any]] = (
            tool_context.state.get("_ag_ui_context") or []
        )
        logger.debug("ag_ui_context: %s", ag_ui_context)
        for ctx in ag_ui_context:
            if ctx.get("description") == "hotel context":
                hotel_context = ctx.get("value")
                if hotel_context:
                    return {
                        "status": "success",
                        "message": "The SPU and SKU information of \
                            room types are included in the result.",
                        "result": json.loads(hotel_context)["roomTypes"],
                    }
        return {
            "status": "error",
            "message": "No hotel context found",
            "result": None,
        }

    async def get_tools(
        self, readonly_context: ReadonlyContext | None = None
    ) -> list[BaseTool]:
        return [self._get_hotel, self._get_room_types]

    async def close(self) -> None:
        return
