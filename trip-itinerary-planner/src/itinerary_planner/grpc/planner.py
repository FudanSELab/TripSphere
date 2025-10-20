"""gRPC servicer for itinerary planning."""

import asyncio
import logging
from typing import Any, AsyncIterator, cast

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc

from itinerary_planner.planning.state import ItineraryState
from itinerary_planner.planning.workflow import ItineraryPlanner

logger = logging.getLogger(__name__)


class ItineraryPlannerServiceServicer(
    itinerary_pb2_grpc.ItineraryPlannerServiceServicer
):
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

    async def PlanItineraryInteractive(
        self,
        request_iterator: AsyncIterator[itinerary_pb2.PlanItineraryInteractiveRequest],
        context: grpc.aio.ServicerContext[
            itinerary_pb2.PlanItineraryInteractiveRequest,
            itinerary_pb2.PlanItineraryInteractiveResponse,
        ],
    ) -> AsyncIterator[itinerary_pb2.PlanItineraryInteractiveResponse]:
        """Plan an itinerary with human-in-the-loop interaction."""
        logger.info("PlanItineraryInteractive request started")

        try:
            # Get the initial request
            first_request = await request_iterator.__anext__()

            if not first_request.HasField("initial_request"):
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "First request must contain initial_request",
                )
                return

            initial = first_request.initial_request

            logger.info(
                f"Planning interactive itinerary for user {initial.user_id} to {initial.destination}"
            )

            # Create a queue to communicate between workflow and gRPC responses
            response_queue: asyncio.Queue[
                itinerary_pb2.PlanItineraryInteractiveResponse | None
            ] = asyncio.Queue()
            user_answer_queue: asyncio.Queue[str] = asyncio.Queue()

            # Start the planning workflow in a background task
            async def run_workflow() -> None:
                try:
                    # Initialize state
                    state: ItineraryState = {
                        "user_id": initial.user_id,
                        "destination": initial.destination,
                        "start_date": initial.start_date,
                        "end_date": initial.end_date,
                        "interests": list(initial.interests),
                        "budget_level": initial.budget_level,
                        "num_travelers": initial.num_travelers,
                        "preferences": dict(initial.preferences),
                        "destination_info": "",
                        "activity_suggestions": [],
                        "daily_schedule": {},
                        "pending_question": None,
                        "user_responses": {},
                        "needs_user_input": False,
                        "itinerary": {},
                        "error": None,
                    }

                    # Send initial status
                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            status_update=itinerary_pb2.StatusUpdate(
                                stage="initializing",
                                message="Starting itinerary planning...",
                                progress_percentage=0,
                            )
                        )
                    )

                    # Run workflow step by step
                    current_state = state

                    # Manually step through the workflow nodes
                    stages = [
                        ("research_destination", "Researching destination", 20),
                        ("check_clarification", "Checking if clarification needed", 30),
                    ]

                    for node_name, stage_msg, progress in stages:
                        await response_queue.put(
                            itinerary_pb2.PlanItineraryInteractiveResponse(
                                status_update=itinerary_pb2.StatusUpdate(
                                    stage=node_name,
                                    message=stage_msg,
                                    progress_percentage=progress,
                                )
                            )
                        )

                        # Execute the node
                        if node_name == "research_destination":
                            from itinerary_planner.planning.nodes import (
                                research_destination,
                            )

                            result = await research_destination(current_state)
                            current_state = cast(
                                ItineraryState, {**current_state, **result}
                            )
                        elif node_name == "check_clarification":
                            from itinerary_planner.planning.nodes import (
                                check_need_clarification,
                            )

                            result = await check_need_clarification(current_state)
                            current_state = cast(
                                ItineraryState, {**current_state, **result}
                            )

                            # Check if we need user input
                            if current_state.get("needs_user_input"):
                                question = current_state.get("pending_question")
                                if question:
                                    # Send question to user
                                    await response_queue.put(
                                        itinerary_pb2.PlanItineraryInteractiveResponse(
                                            question=itinerary_pb2.Question(
                                                question_id=question["question_id"],
                                                question_text=question["question_text"],
                                                suggested_answers=question.get(
                                                    "suggested_answers", []
                                                ),
                                                requires_answer=question.get(
                                                    "requires_answer", True
                                                ),
                                            )
                                        )
                                    )

                                    # Wait for user answer
                                    logger.info("Waiting for user answer...")
                                    answer = await user_answer_queue.get()
                                    logger.info(f"Received user answer: {answer}")

                                    # Store the answer
                                    current_state["user_responses"][
                                        question["question_id"]
                                    ] = answer

                                    # Incorporate response
                                    from itinerary_planner.planning.nodes import (
                                        incorporate_user_response,
                                    )

                                    result = await incorporate_user_response(
                                        current_state
                                    )
                                    current_state = cast(
                                        ItineraryState, {**current_state, **result}
                                    )

                    # Continue with remaining stages
                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            status_update=itinerary_pb2.StatusUpdate(
                                stage="suggest_activities",
                                message="Suggesting activities",
                                progress_percentage=50,
                            )
                        )
                    )

                    from itinerary_planner.planning.nodes import suggest_activities

                    result = await suggest_activities(current_state)
                    current_state = cast(ItineraryState, {**current_state, **result})

                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            status_update=itinerary_pb2.StatusUpdate(
                                stage="create_daily_schedule",
                                message="Creating daily schedule",
                                progress_percentage=70,
                            )
                        )
                    )

                    from itinerary_planner.planning.nodes import create_daily_schedule

                    result = await create_daily_schedule(current_state)
                    current_state = cast(ItineraryState, {**current_state, **result})

                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            status_update=itinerary_pb2.StatusUpdate(
                                stage="finalize_itinerary",
                                message="Finalizing itinerary",
                                progress_percentage=90,
                            )
                        )
                    )

                    from itinerary_planner.planning.nodes import finalize_itinerary

                    result = await finalize_itinerary(current_state)
                    current_state = cast(ItineraryState, {**current_state, **result})

                    # Send final itinerary
                    itinerary = current_state["itinerary"]
                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            final_itinerary=itinerary_pb2.FinalItinerary(
                                itinerary_id=itinerary["id"],
                                itinerary=_dict_to_itinerary_pb(itinerary),
                                message="Itinerary successfully created",
                            )
                        )
                    )

                    # Signal completion
                    await response_queue.put(None)

                except Exception as e:
                    logger.error(f"Error in workflow: {e}", exc_info=True)
                    await response_queue.put(
                        itinerary_pb2.PlanItineraryInteractiveResponse(
                            error=itinerary_pb2.ErrorMessage(
                                error_code="PLANNING_ERROR",
                                error_message=str(e),
                            )
                        )
                    )
                    await response_queue.put(None)

            # Start workflow task
            workflow_task = asyncio.create_task(run_workflow())

            # Handle incoming requests (user responses) and outgoing responses
            async def handle_incoming_requests() -> None:
                async for request in request_iterator:
                    if request.HasField("user_response"):
                        answer = request.user_response.answer
                        await user_answer_queue.put(answer)

            incoming_task = asyncio.create_task(handle_incoming_requests())

            # Stream responses back to client
            while True:
                response = await response_queue.get()
                if response is None:
                    break
                yield response

            # Wait for tasks to complete
            await workflow_task
            incoming_task.cancel()

            logger.info("PlanItineraryInteractive completed successfully")

        except Exception as e:
            logger.error(f"Error in PlanItineraryInteractive: {e}", exc_info=True)
            yield itinerary_pb2.PlanItineraryInteractiveResponse(
                error=itinerary_pb2.ErrorMessage(
                    error_code="INTERNAL_ERROR",
                    error_message=str(e),
                )
            )


def _dict_to_itinerary_pb(itinerary: dict[str, Any]) -> itinerary_pb2.Itinerary:
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
