import logging
from typing import Any

import grpc
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.protobuf.json_format import MessageToDict
from google.rpc import status_pb2  # type: ignore
from grpc_status import rpc_status
from tripsphere.product.v1 import product_pb2, product_pb2_grpc

from order_assistant.nacos.naming import get_nacos_naming

logger = logging.getLogger(__name__)


class ProductToolset(BaseToolset):
    def __init__(self, tool_name_prefix: str = "product_") -> None:
        super().__init__(tool_name_prefix=tool_name_prefix)
        self.service_name = "trip-product-service"
        self._get_spu_by_id = FunctionTool(self.get_spu_by_id)
        self._get_sku_by_id = FunctionTool(self.get_sku_by_id)

    async def _get_server_address(self) -> str:
        try:
            nacos_naming = await get_nacos_naming()
            instance = await nacos_naming.get_service_instance(self.service_name)
        except Exception as e:
            logger.error(f"Failed to get service instance for {self.service_name}: {e}")
            raise e
        grpc_port = instance.metadata.get("gRPC_port", "50060")  # pyright: ignore
        return f"{instance.ip}:{grpc_port}"

    async def get_spu_by_id(self, spu_id: str) -> dict[str, Any]:
        """Get the standard product unit by ID.

        Args:
            spu_id (str): The ID of the standard product unit.

        Returns:
            dict[str, Any]: A dictionary with the spu, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        try:
            server_address = await self._get_server_address()
        except Exception as e:
            return {"status": "error", "message": str(e), "result": None}

        async with grpc.aio.insecure_channel(server_address) as channel:
            stub = product_pb2_grpc.ProductServiceStub(channel)
            try:
                response = await stub.GetSpuById(
                    product_pb2.GetSpuByIdRequest(id=spu_id)
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to get SPU by ID {spu_id}: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # type: ignore
                message = status.message if status else ""  # pyright: ignore
                return {"status": "error", "message": message, "result": None}

        return {
            "status": "success",
            "message": "",
            "result": MessageToDict(response.spu),
        }

    async def get_sku_by_id(self, sku_id: str) -> dict[str, Any]:
        """Get the stock keeping unit by ID.

        Args:
            sku_id (str): The ID of the stock keeping unit.

        Returns:
            dict[str, Any]: A dictionary with the sku, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        try:
            server_address = await self._get_server_address()
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

        return {
            "status": "success",
            "message": "",
            "result": MessageToDict(response.sku),
        }

    async def get_tools(
        self, readonly_context: ReadonlyContext | None = None
    ) -> list[BaseTool]:
        return [self._get_spu_by_id, self._get_sku_by_id]

    async def close(self) -> None:
        # Nacos client shutdown is handled by the application.
        return
