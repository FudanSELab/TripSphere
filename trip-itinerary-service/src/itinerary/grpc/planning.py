import logging
from typing import AsyncIterator

import grpc
from tripsphere.itinerary import planning_pb2, planning_pb2_grpc

logger = logging.getLogger(__name__)


class PlanningServiceServicer(planning_pb2_grpc.PlanningServiceServicer):
    async def PlanItinerary(
        self,
        request: planning_pb2.PlanItineraryRequest,
        context: grpc.aio.ServicerContext[
            planning_pb2.PlanItineraryRequest, planning_pb2.PlanItineraryResponse
        ],
    ) -> planning_pb2.PlanItineraryResponse:
        return planning_pb2.PlanItineraryResponse()

    async def PlanItineraryStream(
        self,
        request: planning_pb2.PlanItineraryStreamRequest,
        context: grpc.aio.ServicerContext[
            planning_pb2.PlanItineraryStreamRequest,
            planning_pb2.PlanItineraryStreamResponse,
        ],
    ) -> AsyncIterator[planning_pb2.PlanItineraryStreamResponse]:
        yield planning_pb2.PlanItineraryStreamResponse()
