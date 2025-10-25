import logging
from typing import AsyncIterator

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

    async def CreateResponseStream(
        self,
        request: response_pb2.CreateResponseRequest,
        context: grpc.aio.ServicerContext[
            response_pb2.CreateResponseRequest,
            response_pb2.CreateResponseStreamResponse,
        ],
    ) -> AsyncIterator[response_pb2.CreateResponseStreamResponse]:
        yield response_pb2.CreateResponseStreamResponse()

    async def GetTask(
        self,
        request: response_pb2.GetTaskRequest,
        context: grpc.aio.ServicerContext[
            response_pb2.GetTaskRequest, response_pb2.GetTaskResponse
        ],
    ) -> response_pb2.GetTaskResponse:
        return response_pb2.GetTaskResponse()

    async def CancelTask(
        self,
        request: response_pb2.CancelTaskRequest,
        context: grpc.aio.ServicerContext[
            response_pb2.CancelTaskRequest, response_pb2.CancelTaskResponse
        ],
    ) -> response_pb2.CancelTaskResponse:
        return response_pb2.CancelTaskResponse()
