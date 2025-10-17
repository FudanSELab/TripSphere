"""gRPC servicer for itinerary planning."""

import logging

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc

from itinerary_planner.planning.workflow import ItineraryPlanner

logger = logging.getLogger(__name__)


class ItineraryPlannerServiceServicer(itinerary_pb2_grpc.ItineraryPlannerServiceServicer):
    """Implementation of the ItineraryPlannerService."""

    def __init__(self) -> None:
        """Initialize the servicer with a planner instance."""
        self.planner = ItineraryPlanner()

    async def PlanItinerary(
        self,
        request: itinerary_pb2.PlanItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.PlanItineraryRequest, itinerary_pb2.PlanItineraryResponse
        ],
    ) -> itinerary_pb2.PlanItineraryResponse:
        """Plan an itinerary based on user preferences."""
        logger.info(
            f"PlanItinerary request from user {request.user_id} for {request.destination}"
        )

        try:
            # Call the planner workflow
            itinerary = await self.planner.plan_itinerary(
                user_id=request.user_id,
                destination=request.destination,
                start_date=request.start_date,
                end_date=request.end_date,
                interests=list(request.interests),
                budget_level=request.budget_level,
                num_travelers=request.num_travelers,
                preferences=dict(request.preferences),
            )

            # Convert to protobuf message
            response = itinerary_pb2.PlanItineraryResponse(
                itinerary_id=itinerary["id"],
                status="success",
                itinerary=_dict_to_itinerary_pb(itinerary),
                message="Itinerary successfully created",
            )

            logger.info(f"Successfully created itinerary {itinerary['id']}")
            return response

        except Exception as e:
            logger.error(f"Error planning itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to plan itinerary: {str(e)}"
            )

    async def RefineItinerary(
        self,
        request: itinerary_pb2.RefineItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.RefineItineraryRequest, itinerary_pb2.RefineItineraryResponse
        ],
    ) -> itinerary_pb2.RefineItineraryResponse:
        """Refine an existing itinerary."""
        logger.info(f"RefineItinerary request for {request.itinerary_id}")

        try:
            # Call the planner refinement
            itinerary = await self.planner.refine_itinerary(
                itinerary_id=request.itinerary_id,
                user_id=request.user_id,
                refinement_instructions=request.refinement_instructions,
                modifications=dict(request.modifications),
            )

            # Convert to protobuf message
            response = itinerary_pb2.RefineItineraryResponse(
                status="success",
                itinerary=_dict_to_itinerary_pb(itinerary),
                message="Itinerary successfully refined",
            )

            logger.info(f"Successfully refined itinerary {request.itinerary_id}")
            return response

        except NotImplementedError:
            await context.abort(
                grpc.StatusCode.UNIMPLEMENTED, "Refinement feature not yet implemented"
            )
        except Exception as e:
            logger.error(f"Error refining itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to refine itinerary: {str(e)}"
            )


def _dict_to_itinerary_pb(itinerary: dict) -> itinerary_pb2.Itinerary:
    """Convert itinerary dictionary to protobuf message."""
    # Convert day plans
    day_plans = []
    for day in itinerary.get("day_plans", []):
        activities = []
        for activity in day.get("activities", []):
            location = activity.get("location", {})
            cost = activity.get("cost", {})

            activities.append(
                itinerary_pb2.Activity(
                    id=activity.get("id", ""),
                    name=activity.get("name", ""),
                    description=activity.get("description", ""),
                    start_time=activity.get("start_time", ""),
                    end_time=activity.get("end_time", ""),
                    location=itinerary_pb2.Location(
                        name=location.get("name", ""),
                        latitude=location.get("latitude", 0.0),
                        longitude=location.get("longitude", 0.0),
                        address=location.get("address", ""),
                    ),
                    category=activity.get("category", ""),
                    cost=itinerary_pb2.EstimatedCost(
                        amount=cost.get("amount", 0.0),
                        currency=cost.get("currency", "USD"),
                    ),
                )
            )

        day_plans.append(
            itinerary_pb2.DayPlan(
                day_number=day.get("day_number", 0),
                date=day.get("date", ""),
                activities=activities,
                notes=day.get("notes", ""),
            )
        )

    # Convert summary
    summary_dict = itinerary.get("summary", {})
    summary = itinerary_pb2.Summary(
        total_estimated_cost=summary_dict.get("total_estimated_cost", 0.0),
        currency=summary_dict.get("currency", "USD"),
        total_activities=summary_dict.get("total_activities", 0),
        highlights=summary_dict.get("highlights", []),
    )

    # Create and return itinerary message
    return itinerary_pb2.Itinerary(
        id=itinerary.get("id", ""),
        destination=itinerary.get("destination", ""),
        start_date=itinerary.get("start_date", ""),
        end_date=itinerary.get("end_date", ""),
        day_plans=day_plans,
        summary=summary,
        created_at=itinerary.get("created_at", ""),
        updated_at=itinerary.get("updated_at", ""),
    )

