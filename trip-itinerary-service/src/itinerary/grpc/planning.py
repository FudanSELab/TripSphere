import logging

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
