import logging

import grpc
from tripsphere.chat import session_pb2, session_pb2_grpc

logger = logging.getLogger(__name__)


class SessionServiceServicer(session_pb2_grpc.SessionServiceServicer):
    async def CreateSession(
        self,
        request: session_pb2.CreateSessionRequest,
        context: grpc.aio.ServicerContext[
            session_pb2.CreateSessionRequest, session_pb2.CreateSessionResponse
        ],
    ) -> session_pb2.CreateSessionResponse:
        return session_pb2.CreateSessionResponse()

    async def DeleteSession(
        self,
        request: session_pb2.DeleteSessionRequest,
        context: grpc.aio.ServicerContext[
            session_pb2.DeleteSessionRequest, session_pb2.DeleteSessionResponse
        ],
    ) -> session_pb2.DeleteSessionResponse:
        return session_pb2.DeleteSessionResponse()

    async def GetSession(
        self,
        request: session_pb2.GetSessionRequest,
        context: grpc.aio.ServicerContext[
            session_pb2.GetSessionRequest, session_pb2.GetSessionResponse
        ],
    ) -> session_pb2.GetSessionResponse:
        return session_pb2.GetSessionResponse()

    async def GetSessionMessages(
        self,
        request: session_pb2.GetSessionMessagesRequest,
        context: grpc.aio.ServicerContext[
            session_pb2.GetSessionMessagesRequest,
            session_pb2.GetSessionMessagesResponse,
        ],
    ) -> session_pb2.GetSessionMessagesResponse:
        return session_pb2.GetSessionMessagesResponse()
