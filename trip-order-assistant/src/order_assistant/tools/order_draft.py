import datetime
import logging
import re
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
from order_assistant.tools.context import build_grpc_metadata, get_current_user_id

logger = logging.getLogger(__name__)


ORDER_DRAFTS: dict[str, dict[str, Any]] = {}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OrderDraftToolset(BaseToolset):
    def __init__(self, tool_name_prefix: str = "order_draft") -> None:
        super().__init__(tool_name_prefix=tool_name_prefix)
        self._create_order_draft = FunctionTool(self.create_order_draft)
        self._get_order_draft = FunctionTool(self.get_order_draft)
        self._delete_order_draft = FunctionTool(self.delete_order_draft)
        self._set_order_draft_contact = FunctionTool(self.set_order_draft_contact)
        self._add_hotel_room_to_draft = FunctionTool(self.add_hotel_room_to_draft)
        self._add_attraction_to_draft = FunctionTool(self.add_attraction_to_draft)
        self._confirm_order_draft = FunctionTool(self.confirm_order_draft)
        self._submit_order_draft = FunctionTool(self.submit_order_draft)

    async def _get_server_address(self, service_name: str) -> str:
        try:
            nacos_naming = await get_nacos_naming()
            instance = await nacos_naming.get_service_instance(service_name)
        except Exception as e:
            logger.error(f"Failed to get service instance for {service_name}: {e}")
            raise e
        grpc_port = instance.metadata.get("gRPC_port")  # pyright: ignore
        if not grpc_port:
            raise RuntimeError(f"Service {service_name} is missing gRPC_port metadata")
        return f"{instance.ip}:{grpc_port}"

    def _get_owned_draft(
        self, order_draft_id: str, tool_context: ToolContext
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        current_user_id = get_current_user_id(tool_context)
        if current_user_id is None:
            return None, {
                "status": "error",
                "message": "User ID is missing in the request context",
                "result": None,
            }

        draft = ORDER_DRAFTS.get(order_draft_id)
        if draft is None:
            return None, {
                "status": "error",
                "message": f"Order draft with ID {order_draft_id} not found",
                "result": None,
            }
        if draft["user_id"] != current_user_id:
            return None, {
                "status": "error",
                "message": "You do not have permission to access this order draft",
                "result": None,
            }
        return draft, None

    def _serialize_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": draft["user_id"],
            "request_id": draft["request_id"],
            "confirmed": draft["confirmed"],
            "contact": dict(draft["contact"]),
            "source": dict(draft["source"]),
            "items": [
                {
                    **item,
                    "date": item["date"].isoformat(),
                    "end_date": (
                        item["end_date"].isoformat()
                        if item["end_date"] is not None
                        else None
                    ),
                }
                for item in draft["items"]
            ],
        }

    async def _get_sellable_sku(
        self, sku_id: str, expected_resource_type: int
    ) -> tuple[dict[str, Any] | None, str | None]:
        try:
            server_address = await self._get_server_address("trip-product-service")
        except Exception as e:
            return None, str(e)

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = product_pb2_grpc.ProductServiceStub(channel)
            try:
                sku_response = await stub.GetSkuById(
                    product_pb2.GetSkuByIdRequest(id=sku_id)
                )
                spu_response = await stub.GetSpuById(
                    product_pb2.GetSpuByIdRequest(id=sku_response.sku.spu_id)
                )
            except grpc.RpcError as e:
                logger.error("Failed to validate SKU %s: %s", sku_id, e)
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else "Product lookup failed"  # pyright: ignore
                return None, message

        if sku_response.sku.status != product_pb2.SKU_STATUS_ACTIVE:
            return None, f"SKU {sku_id} is not active"
        if spu_response.spu.status != product_pb2.SPU_STATUS_ON_SHELF:
            return None, f"SPU for SKU {sku_id} is not on shelf"
        if spu_response.spu.resource_type != expected_resource_type:
            return None, f"SKU {sku_id} does not match the requested resource type"
        return MessageToDict(sku_response.sku), None

    def create_order_draft(self, tool_context: ToolContext) -> dict[str, Any]:
        """Create a new order draft.

        Returns:
            dict[str, Any]: A dictionary with the ID of the created draft, \
                e.g., {"status": "success", "message": "", "result": "<uuid>"}
        """
        order_draft_id = str(uuid4())
        user_id = get_current_user_id(tool_context)
        if user_id is None:
            return {
                "status": "error",
                "message": "User ID is missing in the headers",
                "result": None,
            }
        ORDER_DRAFTS[order_draft_id] = {
            "user_id": user_id,
            "request_id": str(uuid4()),
            "items": [],
            "confirmed": False,
            "source": {
                "channel": "agent",
                "agent_id": "order_assistant",
                "session_id": tool_context.session.id,
            },
            "contact": {"name": "", "phone": "", "email": ""},
        }
        return {
            "status": "success",
            "message": (
                "Order draft created successfully. "
                f"Use this ID {order_draft_id} to modify the draft later."
            ),
            "result": order_draft_id,
        }

    def get_order_draft(
        self, order_draft_id: str, tool_context: ToolContext
    ) -> dict[str, Any]:
        """Get the order draft by ID.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the order draft, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        assert draft is not None
        return {
            "status": "success",
            "message": "",
            "result": self._serialize_draft(draft),
        }

    def delete_order_draft(
        self, order_draft_id: str, tool_context: ToolContext
    ) -> dict[str, Any]:
        """Delete the order draft by ID.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the ID of the deleted draft, \
                e.g., {"status": "success", "message": "", "result": "<uuid>"}
        """
        _, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        del ORDER_DRAFTS[order_draft_id]
        return {
            "status": "success",
            "message": f"Order draft with ID {order_draft_id} deleted successfully.",
            "result": order_draft_id,
        }

    def set_order_draft_contact(
        self,
        order_draft_id: str,
        name: str,
        phone: str,
        email: str,
        tool_context: ToolContext,
    ) -> dict[str, Any]:
        """Set the contact information used when an order draft is submitted."""
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        if not name.strip() or not phone.strip() or not EMAIL_PATTERN.fullmatch(email.strip()):
            return {
                "status": "error",
                "message": "A contact name, phone number, and valid email are required",
                "result": None,
            }

        assert draft is not None
        draft["contact"] = {
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
        }
        draft["confirmed"] = False
        return {
            "status": "success",
            "message": "Order draft contact updated successfully.",
            "result": draft["contact"],
        }

    async def add_hotel_room_to_draft(
        self,
        order_draft_id: str,
        sku_id: str,
        start_date: str,
        end_date: str,
        quantity: int,
        tool_context: ToolContext,
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
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        if quantity <= 0:
            return {
                "status": "error",
                "message": "Quantity must be greater than zero",
                "result": None,
            }
        try:
            parsed_start_date = datetime.date.fromisoformat(start_date)
            parsed_end_date = datetime.date.fromisoformat(end_date)
        except ValueError:
            return {
                "status": "error",
                "message": "Hotel dates must use ISO 8601 format (YYYY-MM-DD)",
                "result": None,
            }
        if parsed_start_date < datetime.date.today():
            return {
                "status": "error",
                "message": "Check-in date must not be in the past",
                "result": None,
            }
        if parsed_end_date <= parsed_start_date:
            return {
                "status": "error",
                "message": "Check-out date must be after check-in date",
                "result": None,
            }

        sku, product_error = await self._get_sellable_sku(
            sku_id, product_pb2.RESOURCE_TYPE_HOTEL_ROOM
        )
        if product_error is not None:
            return {"status": "error", "message": product_error, "result": None}

        assert draft is not None
        draft["items"].append(
            {
                "sku_id": sku_id,
                "date": parsed_start_date,
                "end_date": parsed_end_date,
                "quantity": quantity,
            }
        )
        draft["confirmed"] = False

        return {
            "status": "success",
            "message": f"Hotel room SKU {sku_id} added to order draft successfully.",
            "result": sku,
        }

    async def add_attraction_to_draft(
        self,
        order_draft_id: str,
        sku_id: str,
        date: str,
        quantity: int,
        tool_context: ToolContext,
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
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        if quantity <= 0:
            return {
                "status": "error",
                "message": "Quantity must be greater than zero",
                "result": None,
            }
        try:
            parsed_date = datetime.date.fromisoformat(date)
        except ValueError:
            return {
                "status": "error",
                "message": "Attraction date must use ISO 8601 format (YYYY-MM-DD)",
                "result": None,
            }
        if parsed_date < datetime.date.today():
            return {
                "status": "error",
                "message": "Attraction date must not be in the past",
                "result": None,
            }

        sku, product_error = await self._get_sellable_sku(
            sku_id, product_pb2.RESOURCE_TYPE_ATTRACTION
        )
        if product_error is not None:
            return {"status": "error", "message": product_error, "result": None}

        assert draft is not None
        draft["items"].append(
            {
                "sku_id": sku_id,
                "date": parsed_date,
                "end_date": None,
                "quantity": quantity,
            }
        )
        draft["confirmed"] = False

        return {
            "status": "success",
            "message": f"Attraction SKU {sku_id} added to order draft successfully.",
            "result": sku,
        }

    def confirm_order_draft(
        self, order_draft_id: str, tool_context: ToolContext
    ) -> dict[str, Any]:
        """Confirm a complete order draft before it can be submitted."""
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error

        assert draft is not None
        contact = draft["contact"]
        if (
            not contact["name"]
            or not contact["phone"]
            or not EMAIL_PATTERN.fullmatch(contact["email"])
        ):
            return {
                "status": "error",
                "message": "Complete contact information is required before confirmation",
                "result": None,
            }
        if not draft["items"]:
            return {
                "status": "error",
                "message": "At least one order item is required before confirmation",
                "result": None,
            }

        draft["confirmed"] = True
        return {
            "status": "success",
            "message": "Order draft confirmed and ready for submission.",
            "result": self._serialize_draft(draft),
        }

    def _create_order_item(self, item: dict[str, Any]) -> order_pb2.CreateOrderItem:
        date = date_to_proto(item["date"])
        if date is None:
            raise ValueError("Order item date is required")
        proto_item = order_pb2.CreateOrderItem(
            sku_id=item["sku_id"],
            date=date,
            quantity=item["quantity"],
        )
        end_date = date_to_proto(item["end_date"])
        if end_date is not None:
            proto_item.end_date.CopyFrom(end_date)
        return proto_item

    async def submit_order_draft(
        self, order_draft_id: str, tool_context: ToolContext
    ) -> dict[str, Any]:
        """Submit the order draft to place the order.

        Args:
            order_draft_id (str): The ID of the order draft.

        Returns:
            dict[str, Any]: A dictionary with the created order, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        draft, error = self._get_owned_draft(order_draft_id, tool_context)
        if error is not None:
            return error
        assert draft is not None
        if not draft["confirmed"]:
            return {
                "status": "error",
                "message": "Order draft must be confirmed before submission",
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
                        user_id=draft["user_id"],
                        request_id=draft["request_id"],
                        items=[
                            self._create_order_item(item) for item in draft["items"]
                        ],
                        contact=contact_info_to_proto(draft["contact"]),
                        source=order_source_to_proto(draft["source"]),
                    ),
                    metadata=build_grpc_metadata(tool_context),
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to create order: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else ""  # pyright: ignore
                return {"status": "error", "message": message, "result": None}

        del ORDER_DRAFTS[order_draft_id]
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
            self._set_order_draft_contact,
            self._add_hotel_room_to_draft,
            self._add_attraction_to_draft,
            self._confirm_order_draft,
            self._submit_order_draft,
        ]

    async def close(self) -> None:
        # Nacos client shutdown is handled by the application.
        return
