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

        # Plan itinerary
        await plan_itinerary_example()

    except grpc.aio.AioRpcError as e:
        logger.error(f"gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
