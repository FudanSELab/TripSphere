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

from journey_assistant.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)


class ProductToolset(BaseToolset):
    def __init__(self, nacos_naming: NacosNaming) -> None:
        self.nacos_naming = nacos_naming
        self.service_name = "trip-product-service"
        self._get_spu_by_id = FunctionTool(self.get_spu_by_id)

    async def get_spu_by_id(self, spu_id: str) -> dict[str, Any]:
        """Get the standard product unit by ID.

        Args:
            spu_id (str): The ID of the standard product unit.

        Returns:
            dict[str, Any]: A dictionary with the spu, \
                e.g., {"status": "success", "message": "", "result": {...}}
        """
        try:
            instance = await self.nacos_naming.get_service_instance(self.service_name)
        except RuntimeError as e:
            logger.error(f"Failed to get service instance for {self.service_name}: {e}")
            return {"status": "error", "message": str(e), "result": None}

        target = f"{instance.ip}:{instance.port}"
        async with grpc.aio.insecure_channel(target) as channel:
            stub = product_pb2_grpc.ProductServiceStub(channel)
            try:
                response = await stub.GetSpuById(
                    product_pb2.GetSpuByIdRequest(id=spu_id)
                )
            except grpc.RpcError as e:
                logger.error(f"Failed to get SPU by ID {spu_id}: {e}")
                status: status_pb2.Status = rpc_status.from_call(e)  # pyright: ignore
                return {"status": "error", "message": status.message, "result": None}  # pyright: ignore
            return {
                "status": "success",
                "message": "",
                "result": MessageToDict(response.spu),
            }

    async def get_tools(
        self, readonly_context: ReadonlyContext | None = None
    ) -> list[BaseTool]:
        return [self._get_spu_by_id]

    async def close(self) -> None:
        return
