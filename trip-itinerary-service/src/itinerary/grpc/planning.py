import logging
from typing import AsyncIterator

import grpc
import httpx
from a2a.client import A2AClient
from tripsphere.itinerary import planning_pb2, planning_pb2_grpc

from itinerary.itinerary.repositories import ItineraryRepository
from itinerary.nacos.ai import NacosAI

logger = logging.getLogger(__name__)


class PlanningServiceServicer(planning_pb2_grpc.PlanningServiceServicer):
    """Planning service that calls trip-itinerary-planner via A2A protocol."""

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        repository: ItineraryRepository,
        nacos_ai: NacosAI,
    ) -> None:
        self.httpx_client = httpx_client
        self.repository = repository
        self.nacos_ai = nacos_ai
        logger.info("PlanningServiceServicer initialized")

    async def _get_a2a_client(self) -> A2AClient:
        try:
            agent_card = await self.nacos_ai.get_agent_card("itinerary_planner")
            logger.info(
                f"Fetched agent card: {agent_card.name} version {agent_card.version}"
            )
        except Exception as e:
            logger.error(f"Failed to get A2A client: {e}", exc_info=True)
            raise RuntimeError(f"Cannot connect to itinerary planner agent: {e}") from e
        return A2AClient(httpx_client=self.httpx_client, agent_card=agent_card)

    async def PlanItinerary(
        self,
        request: planning_pb2.PlanItineraryRequest,
        context: grpc.aio.ServicerContext[
            planning_pb2.PlanItineraryRequest, planning_pb2.PlanItineraryResponse
        ],
    ) -> planning_pb2.PlanItineraryResponse:
        raise NotImplementedError

    async def PlanItineraryStream(
        self,
        request: planning_pb2.PlanItineraryStreamRequest,
        context: grpc.aio.ServicerContext[
            planning_pb2.PlanItineraryStreamRequest,
            planning_pb2.PlanItineraryStreamResponse,
        ],
    ) -> AsyncIterator[planning_pb2.PlanItineraryStreamResponse]:
        """Plan an itinerary with streaming progress updates."""

        logger.info(
            "Received streaming itinerary planning request "
            f"for {request.user_id} with destination {request.destination}"
        )

        try:
            _ = await self._get_a2a_client()  # TODO: Implement A2A client logic

        except Exception as e:
            logger.error(f"Error during streaming planning: {e}", exc_info=True)
            # Yield error response
            yield planning_pb2.PlanItineraryStreamResponse(
                progress_percentage=0,
                status_message=f"Planning failed: {str(e)}",
                current_step=planning_pb2.PlanItineraryStreamResponse.PLANNING_STEP_UNSPECIFIED,
            )
