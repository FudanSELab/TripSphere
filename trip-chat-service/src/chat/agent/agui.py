import json
import logging
from typing import Any

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


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
