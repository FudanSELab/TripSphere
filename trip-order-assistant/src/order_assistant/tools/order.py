import logging
from typing import Any

import grpc
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.protobuf.json_format import MessageToDict
from tripsphere.order.v1 import order_pb2, order_pb2_grpc

from order_assistant.nacos.naming import get_nacos_naming

logger = logging.getLogger(__name__)


class OrderToolset(BaseToolset):
    def __init__(self, tool_name_prefix: str = "order_") -> None:
        super().__init__(tool_name_prefix=tool_name_prefix)
        self.service_name = "trip-order-service"
        self._get_order = FunctionTool(self.get_order)
        self._cancel_order = FunctionTool(self.cancel_order)

    async def _get_server_address(self) -> str:
        try:
            nacos_naming = await get_nacos_naming()
            instance = await nacos_naming.get_service_instance(self.service_name)
        except Exception as e:
            logger.error(f"Failed to get service instance for {self.service_name}: {e}")
            raise e
        grpc_port = instance.metadata.get("gRPC_port", "50062")  # pyright: ignore
        return f"{instance.ip}:{grpc_port}"

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """Get the order by order ID.

        Args:
            order_id (str): The ID of the order.

        Returns:
            dict[str, Any]: A dictionary with the order, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        try:
            server_address = await self._get_server_address()
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = order_pb2_grpc.OrderServiceStub(channel)
            try:
                response = await stub.GetOrder(order_pb2.GetOrderRequest(id=order_id))
            except grpc.RpcError as e:
                logger.error(f"Failed to get order by ID {order_id}: {e}")
                message = e.details() or ""
                return {"status": "error", "message": message, "result": None}

        return {
            "status": "success",
            "message": "",
            "result": MessageToDict(response.order),
        }

    async def cancel_order(self, order_id: str, reason: str) -> dict[str, Any]:
        """Cancel a order by order ID.

        Args:
            order_id (str): The ID of the order.
            reason (str): The reason for canceling the order.

        Returns:
            dict[str, Any]: A dictionary with the order, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        try:
            server_address = await self._get_server_address()
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = order_pb2_grpc.OrderServiceStub(channel)
            try:
                response = await stub.CancelOrder(
                    order_pb2.CancelOrderRequest(order_id=order_id, reason=reason)
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to cancel order by ID {order_id}: {e}")
                message = e.details() or ""
                return {"status": "error", "message": message, "result": None}

        return {
            "status": "success",
            "message": f"Order {order_id} has been cancelled successfully.",
            "result": MessageToDict(response.order),
        }

    async def get_tools(
        self, readonly_context: ReadonlyContext | None = None
    ) -> list[BaseTool]:
        return [self._get_order, self._cancel_order]

    async def close(self) -> None:
        # Nacos client shutdown is handled by the application.
        return
