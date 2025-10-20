import asyncio
import logging

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def plan_itinerary_example():
    async with grpc.aio.insecure_channel("localhost:50059") as channel:
        stub = itinerary_pb2_grpc.ItineraryPlannerServiceStub(channel)

        # Create request
        # request = itinerary_pb2.PlanItineraryRequest(
        #     user_id="user123",
        #     destination="Paris, France",
        #     start_date="2025-06-01",
        #     end_date="2025-06-05",
        #     interests=["culture", "food", "art", "history"],
        #     budget_level="moderate",
        #     num_travelers=2,
        #     preferences={
        #         "accommodation_area": "Le Marais",
        #         "dietary_restrictions": "vegetarian-friendly",
        #     },
        # )

        request = itinerary_pb2.PlanItineraryRequest(
            user_id="user123",
            destination="Chengdu, China",
            start_date="2025-10-30",
            end_date="2025-11-04",
            interests=["food", "nature"],
            budget_level="moderate",
            num_travelers=4,
            preferences={
                "accommodation_area": "Chengdu",
                "dietary_restrictions": "no restrictions",
            },
        )

        logger.info(f"Planning itinerary for {request.destination}...")
        response = await stub.PlanItinerary(request)

        logger.info(f"Status: {response.status}")
        logger.info(f"Itinerary ID: {response.itinerary_id}")
        logger.info(f"Message: {response.message}")

        itinerary = response.itinerary
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Destination: {itinerary.destination}")
        logger.info(f"Dates: {itinerary.start_date} to {itinerary.end_date}")
        logger.info(f"Total Activities: {itinerary.summary.total_activities}")
        logger.info(
            f"Estimated Cost: ${itinerary.summary.total_estimated_cost:.2f} {itinerary.summary.currency}"  # noqa: E501
        )

        logger.info("\nHighlights:")
        for highlight in itinerary.summary.highlights:
            logger.info(f"  • {highlight}")

        logger.info("\nDaily Itinerary:")
        for day in itinerary.day_plans:
            logger.info(f"\n  Day {day.day_number} - {day.date}")
            logger.info(f"  {day.notes}")
            for activity in day.activities:
                logger.info(f"    {activity.start_time}-{activity.end_time}: {activity.name}")
                logger.info(f"      Location: {activity.location.name}")
                logger.info(f"      Cost: ${activity.cost.amount:.2f} {activity.cost.currency}")

        logger.info(f"\n{'=' * 60}")


async def plan_itinerary_interactive_example():
    """Example of planning an itinerary with human-in-the-loop interaction."""
    async with grpc.aio.insecure_channel("localhost:50059") as channel:
        stub = itinerary_pb2_grpc.ItineraryPlannerServiceStub(channel)

        # Create a queue for sending requests
        request_queue = asyncio.Queue()

        # Send initial request
        initial_request = itinerary_pb2.PlanItineraryInteractiveRequest(
            initial_request=itinerary_pb2.InitialRequest(
                user_id="user456",
                destination="Tokyo, Japan",
                start_date="2025-12-01",
                end_date="2025-12-05",
                interests=["culture", "technology"],
                budget_level="moderate",
                num_travelers=2,
                preferences={},
            )
        )
        await request_queue.put(initial_request)

        async def request_generator():
            """Generate requests from the queue."""
            while True:
                request = await request_queue.get()
                if request is None:
                    break
                yield request

        # Call the streaming RPC
        logger.info("Starting interactive itinerary planning...")
        logger.info("=" * 60)

        response_stream = stub.PlanItineraryInteractive(request_generator())

        try:
            async for response in response_stream:
                if response.HasField("status_update"):
                    status = response.status_update
                    logger.info(f"[{status.progress_percentage}%] {status.stage}: {status.message}")

                elif response.HasField("question"):
                    question = response.question
                    logger.info("\n" + "=" * 60)
                    logger.info("🤔 Question from planner:")
                    logger.info(f"   {question.question_text}")

                    if question.suggested_answers:
                        logger.info("\n   Suggested answers:")
                        for i, answer in enumerate(question.suggested_answers, 1):
                            logger.info(f"   {i}. {answer}")

                    # Simulate user input (in real scenario, get input from user)
                    logger.info("\n   💭 Thinking... (simulating user response)")
                    await asyncio.sleep(1)  # Simulate thinking time

                    # Auto-respond with a simulated answer
                    user_answer = "I prefer a relaxed pace with some time for spontaneous exploration. I'd like to visit traditional temples and modern tech districts."
                    logger.info(f"   ✅ User response: {user_answer}")
                    logger.info("=" * 60 + "\n")

                    # Send user response
                    user_response = itinerary_pb2.PlanItineraryInteractiveRequest(
                        user_response=itinerary_pb2.UserResponse(
                            question_id=question.question_id,
                            answer=user_answer,
                        )
                    )
                    await request_queue.put(user_response)

                elif response.HasField("final_itinerary"):
                    final = response.final_itinerary
                    logger.info("\n" + "=" * 60)
                    logger.info("✨ Itinerary completed!")
                    logger.info(f"Itinerary ID: {final.itinerary_id}")
                    logger.info(f"Message: {final.message}")

                    itinerary = final.itinerary
                    logger.info(f"\nDestination: {itinerary.destination}")
                    logger.info(f"Dates: {itinerary.start_date} to {itinerary.end_date}")
                    logger.info(f"Total Activities: {itinerary.summary.total_activities}")
                    logger.info(f"Estimated Cost: ${itinerary.summary.total_estimated_cost:.2f} {itinerary.summary.currency}")

                    logger.info("\nHighlights:")
                    for highlight in itinerary.summary.highlights:
                        logger.info(f"  • {highlight}")

                    logger.info("\nDaily Itinerary:")
                    for day in itinerary.day_plans:
                        logger.info(f"\n  Day {day.day_number} - {day.date}")
                        for activity in day.activities:
                            logger.info(f"    {activity.start_time}-{activity.end_time}: {activity.name}")
                            logger.info(f"      📍 {activity.location.name}")
                            logger.info(f"      💵 ${activity.cost.amount:.2f}")

                    logger.info("=" * 60)

                elif response.HasField("error"):
                    error = response.error
                    logger.error(f"❌ Error: [{error.error_code}] {error.error_message}")

        finally:
            # Signal end of requests
            await request_queue.put(None)


async def get_version_example():
    """Example of getting the service version."""
    async with grpc.aio.insecure_channel("localhost:50059") as channel:
        # Import metadata
        from tripsphere.itinerary import metadata_pb2, metadata_pb2_grpc

        stub = metadata_pb2_grpc.MetadataServiceStub(channel)
        request = metadata_pb2.GetVersionRequest()

        response = await stub.GetVersion(request)
        logger.info(f"Service Version: {response.version}")


async def main():
    """Run examples."""
    try:
        # Get version
        await get_version_example()

        # Choose which example to run
        logger.info("\n" + "=" * 60)
        logger.info("Running interactive itinerary planning example...")
        logger.info("=" * 60 + "\n")

        # Plan itinerary with human-in-the-loop
        await plan_itinerary_interactive_example()

        # Uncomment to run standard planning instead:
        # await plan_itinerary_example()

    except grpc.aio.AioRpcError as e:
        logger.error(f"gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
