import logging

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc

logger = logging.getLogger(__name__)


class ItineraryServiceServicer(itinerary_pb2_grpc.ItineraryServiceServicer):
    async def CreateItinerary(
        self,
        request: itinerary_pb2.CreateItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.CreateItineraryRequest, itinerary_pb2.CreateItineraryResponse
        ],
    ) -> itinerary_pb2.CreateItineraryResponse:
        return itinerary_pb2.CreateItineraryResponse()

    async def GetItinerary(
        self,
        request: itinerary_pb2.GetItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.GetItineraryRequest, itinerary_pb2.GetItineraryResponse
        ],
    ) -> itinerary_pb2.GetItineraryResponse:
        return itinerary_pb2.GetItineraryResponse()

    async def DeleteItinerary(
        self,
        request: itinerary_pb2.DeleteItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.DeleteItineraryRequest, itinerary_pb2.DeleteItineraryResponse
        ],
    ) -> itinerary_pb2.DeleteItineraryResponse:
        return itinerary_pb2.DeleteItineraryResponse()
