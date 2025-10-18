import logging

import grpc
from tripsphere.chat import conversation_pb2, conversation_pb2_grpc

logger = logging.getLogger(__name__)


class ConversationServiceServicer(conversation_pb2_grpc.ConversationServiceServicer):
    async def CreateConversation(
        self,
        request: conversation_pb2.CreateConversationRequest,
        context: grpc.aio.ServicerContext[
            conversation_pb2.CreateConversationRequest,
            conversation_pb2.CreateConversationResponse,
        ],
    ) -> conversation_pb2.CreateConversationResponse:
        metadata = context.invocation_metadata()
        metadata = dict(metadata) if metadata else {}
        user_id = metadata.get("x-user-id", "")
        logger.info(f"Creating conversation for user_id {user_id}")
        return conversation_pb2.CreateConversationResponse()

    async def DeleteConversation(
        self,
        request: conversation_pb2.DeleteConversationRequest,
        context: grpc.aio.ServicerContext[
            conversation_pb2.DeleteConversationRequest,
            conversation_pb2.DeleteConversationResponse,
        ],
    ) -> conversation_pb2.DeleteConversationResponse:
        return conversation_pb2.DeleteConversationResponse()

    async def GetConversation(
        self,
        request: conversation_pb2.GetConversationRequest,
        context: grpc.aio.ServicerContext[
            conversation_pb2.GetConversationRequest,
            conversation_pb2.GetConversationResponse,
        ],
    ) -> conversation_pb2.GetConversationResponse:
        return conversation_pb2.GetConversationResponse()
