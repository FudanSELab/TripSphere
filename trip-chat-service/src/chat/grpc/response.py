import logging

import grpc
from tripsphere.chat import response_pb2, response_pb2_grpc

logger = logging.getLogger(__name__)


class ResponseServiceServicer(response_pb2_grpc.ResponseServiceServicer):
    async def CreateResponse(
        self,
        request: response_pb2.CreateResponseRequest,
        context: grpc.aio.ServicerContext[
            response_pb2.CreateResponseRequest, response_pb2.CreateResponseResponse
        ],
    ) -> response_pb2.CreateResponseResponse:
        return response_pb2.CreateResponseResponse()
