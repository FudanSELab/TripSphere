import datetime
import logging
from typing import Any
from uuid import uuid4

import grpc
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.protobuf.json_format import MessageToDict
from google.rpc import status_pb2  # type: ignore
from grpc_status import rpc_status
from tripsphere.order.v1 import order_pb2, order_pb2_grpc
from tripsphere.product.v1 import product_pb2, product_pb2_grpc

from order_assistant.mappers.common_mapper import date_to_proto
from order_assistant.mappers.order_mapper import (
    contact_info_to_proto,
    order_source_to_proto,
)
from order_assistant.nacos.naming import get_nacos_naming

logger = logging.getLogger(__name__)


ORDER_DRAFTS: dict[str, dict[str, Any]] = {}


class OrderDraftToolset(BaseToolset):
    def __init__(self, tool_name_prefix: str = "order_draft_") -> None:
        super().__init__(tool_name_prefix=tool_name_prefix)
        self._create_order_draft = FunctionTool(self.create_order_draft)
        self._get_order_draft = FunctionTool(self.get_order_draft)
        self._delete_order_draft = FunctionTool(self.delete_order_draft)
        self._add_hotel_room_to_draft = FunctionTool(self.add_hotel_room_to_draft)
        self._add_attraction_to_draft = FunctionTool(self.add_attraction_to_draft)
        self._submit_order_draft = FunctionTool(self.submit_order_draft)

    async def _get_server_address(self, service_name: str) -> str:
        try:
            nacos_naming = await get_nacos_naming()
            instance = await nacos_naming.get_service_instance(service_name)
        except Exception as e:
            logger.error(f"Failed to get service instance for {service_name}: {e}")
            raise e
        grpc_port = instance.metadata.get("gRPC_port")  # pyright: ignore
        return f"{instance.ip}:{grpc_port}"

    def create_order_draft(self, tool_context: ToolContext) -> dict[str, Any]:
        """Create a new order draft.
        User should confirm the contact information before creating the order draft.
        Submit the order draft to create the real order.

        Returns:
            dict[str, Any]: A dictionary with the ID of the created draft, \
                e.g., {"status": "success", "message": "", "result": "<uuid>"}
        """
        order_draft_id = str(uuid4())
        ORDER_DRAFTS[order_draft_id] = {
            # TODO: get user ID from context
            "user_id": "019cb936-58c6-7ddf-9200-f8ad32140a05",
            "items": [],
            "source": {
                "channel": "web",  # Only web channel is supported for now.
                "agent_id": "order-assistant",
                "session_id": tool_context.session.id,
            },
            # TODO: get contact information from confirmation
            "contact": {
                "name": "谢森煜",
                "phone": "15159596227",
                "email": "senyuxie@qq.com",
            },
        }
        return {
            "status": "success",
            "message": (
                "Order draft created successfully. "
                f"Use this ID {order_draft_id} to modify the draft later."
            ),
            "result": order_draft_id,
        }

    def get_order_draft(self, order_draft_id: str) -> dict[str, Any]:
        """Get the order draft by ID.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the order draft, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        if order_draft_id not in ORDER_DRAFTS:
            return {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }
        return {
            "status": "success",
            "message": "",
            "result": ORDER_DRAFTS[order_draft_id],
        }

    def delete_order_draft(self, order_draft_id: str) -> dict[str, Any]:
        """Delete the order draft by ID.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the ID of the deleted draft, \
                e.g., {"status": "success", "message": "", "result": "<uuid>"}
        """
        if order_draft_id not in ORDER_DRAFTS:
            return {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }
        del ORDER_DRAFTS[order_draft_id]
        return {
            "status": "success",
            "message": f"Order draft with ID {order_draft_id} deleted successfully.",
            "result": order_draft_id,
        }

    async def add_hotel_room_to_draft(
        self,
        order_draft_id: str,
        sku_id: str,
        start_date: str,
        end_date: str,
        quantity: int,
    ) -> dict[str, Any]:
        """Add a hotel room SKU to the order draft.

        Args:
            order_draft_id (str): The ID of the order draft.
            sku_id (str): The ID of the hotel room SKU.
            start_date (str): The ISO8601 check in date.
            end_date (str): The ISO8601 check out date.
            quantity (int): The quantity of the hotel rooms to reserve.

        Returns:
            dict[str, Any]: A dictionary with the added hotel room SKU, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        if order_draft_id not in ORDER_DRAFTS:
            return {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }

        try:
            server_address = await self._get_server_address("trip-product-service")
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = product_pb2_grpc.ProductServiceStub(channel)
            try:
                response = await stub.GetSkuById(
                    product_pb2.GetSkuByIdRequest(id=sku_id)
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to get SKU by ID {sku_id}: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else ""  # pyright: ignore
                return {"status": "error", "message": message, "result": None}

        ORDER_DRAFTS[order_draft_id]["items"].append(
            {
                "sku_id": sku_id,
                "date": datetime.date.fromisoformat(start_date),
                "end_date": datetime.date.fromisoformat(end_date),
                "quantity": quantity,
            }
        )

        return {
            "status": "success",
            "message": f"Hotel room SKU {sku_id} added to order draft successfully.",
            "result": MessageToDict(response.sku),
        }

    async def add_attraction_to_draft(
        self, order_draft_id: str, sku_id: str, date: str, quantity: int
    ) -> dict[str, Any]:
        """Add an attraction SKU to the order draft.

        Args:
            order_draft_id (str): The ID of the order draft.
            sku_id (str): The ID of the attraction SKU.
            date (str): The ISO8601 date of the attraction ticket.
            quantity (int): The quantity of the attraction ticket.

        Returns:
            dict[str, Any]: A dictionary with the added attraction SKU, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        if order_draft_id not in ORDER_DRAFTS:
            return {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }

        try:
            server_address = await self._get_server_address("trip-product-service")
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = product_pb2_grpc.ProductServiceStub(channel)
            try:
                response = await stub.GetSkuById(
                    product_pb2.GetSkuByIdRequest(id=sku_id)
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to get SKU by ID {sku_id}: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else ""  # pyright: ignore
                return {"status": "error", "message": message, "result": None}

        ORDER_DRAFTS[order_draft_id]["items"].append(
            {
                "sku_id": sku_id,
                "date": datetime.date.fromisoformat(date),
                "end_date": None,
                "quantity": quantity,
            }
        )

        return {
            "status": "success",
            "message": f"Attraction SKU {sku_id} added to order draft successfully.",
            "result": MessageToDict(response.sku),
        }

    async def submit_order_draft(self, order_draft_id: str) -> dict[str, Any]:
        """Submit the order draft to place the order.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the created order, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        if order_draft_id not in ORDER_DRAFTS:
            return {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }

        try:
            server_address = await self._get_server_address("trip-order-service")
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = order_pb2_grpc.OrderServiceStub(channel)
            try:
                response = await stub.CreateOrder(
                    order_pb2.CreateOrderRequest(
                        user_id=ORDER_DRAFTS[order_draft_id]["user_id"],
                        items=[
                            order_pb2.CreateOrderItem(
                                sku_id=item["sku_id"],
                                date=date_to_proto(item["date"]),
                                end_date=date_to_proto(item["end_date"]),
                                quantity=item["quantity"],
                            )
                            for item in ORDER_DRAFTS[order_draft_id]["items"]
                        ],
                        contact=contact_info_to_proto(
                            ORDER_DRAFTS[order_draft_id]["contact"]
                        ),
                        source=order_source_to_proto(
                            ORDER_DRAFTS[order_draft_id]["source"]
                        ),
                    )
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to create order: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else ""  # pyright: ignore
                return {"status": "error", "message": message, "result": None}

        return {
            "status": "success",
            "message": f"Order submitted successfully. Order ID: {response.order.id}",
            "result": MessageToDict(response.order),
        }

    async def get_tools(
        self, readonly_context: ReadonlyContext | None = None
    ) -> list[BaseTool]:
        return [
            self._create_order_draft,
            self._get_order_draft,
            self._delete_order_draft,
            self._add_hotel_room_to_draft,
            self._add_attraction_to_draft,
            self._submit_order_draft,
        ]

    async def close(self) -> None:
        # Nacos client shutdown is handled by the application.
        return
