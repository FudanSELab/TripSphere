import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from itinerary_planner.agent.state import PlanningState
from itinerary_planner.agent.workflow import create_planning_workflow
from itinerary_planner.models.itinerary import TravelInterest, TripPace

# Set up basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_workflow():
    """Test the itinerary planning workflow with sample data."""

    # Set up basic environment variables (you may need to adjust these)
    if "OPENAI_API_KEY" not in os.environ:
        logger.warning("OPENAI_API_KEY not set. Please set it to run the workflow.")
        # For testing, you can uncomment and set your API key:
        # os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'

    # Create test input data
    today = datetime.now().date()
    start_date = today + timedelta(days=7)  # 1 week from now
    end_date = start_date + timedelta(days=2)  # 3-day trip

    initial_state: PlanningState = {
        "user_id": "test-user-123",
        "destination": "Shanghai",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "interests": [TravelInterest.CULTURE],
        "pace": TripPace.MODERATE,
        "additional_preferences": ("I prefer walking tours and local experiences."),
        # Initialize empty fields
        "destination_info": "",
        "destination_coords": {},
        "activity_suggestions": [],
        "attraction_details": {},
        "daily_schedule": {},
        "itinerary": None,
        "error": None,
        "events": [],
    }

    logger.info(f"Testing workflow with destination: {initial_state['destination']}")
    logger.info(
        f"Trip dates: {initial_state['start_date']} to {initial_state['end_date']}"
    )
    logger.info(
        f"Interests: {[interest.value for interest in initial_state['interests']]}"
    )
    logger.info(f"Pace: {initial_state['pace'].value}")

    try:
        # Create the workflow
        workflow = create_planning_workflow()
        logger.info("Workflow created successfully")

        # Run the workflow
        logger.info("Starting workflow execution...")
        result = await workflow.ainvoke(initial_state)

        # Print results
        print("\n" + "=" * 80)
        print("WORKFLOW EXECUTION RESULTS")
        print("=" * 80)

        print(f"\nDestination: {result.get('destination', 'N/A')}")
        print(
            f"Dates: {result.get('start_date', 'N/A')} to "
            f"{result.get('end_date', 'N/A')}"
        )

        if result.get("error"):
            print(f"\nERROR: {result['error']}")
        else:
            print("\nSUCCESS: Workflow completed without errors")

        # Show destination info
        if result.get("destination_info"):
            print(f"\nDestination Info: {result['destination_info'][:200]}...")

        # Show coordinates
        if result.get("destination_coords"):
            coords = result["destination_coords"]
            print(
                f"\nDestination Coordinates: {coords.get('longitude')},"
                f" {coords.get('latitude')}"
            )
            print(f"Address: {coords.get('address')}")

        # Show activity suggestions count
        if result.get("activity_suggestions"):
            print(
                f"\nActivity Suggestions: {len(result['activity_suggestions'])} found"
            )

        # Show itinerary
        if result.get("itinerary"):
            itinerary = result["itinerary"]
            with open("itinerary.json", "w") as f:
                json.dump(itinerary.model_dump(), f, indent=4)
            print(f"Itinerary Summary {itinerary.summary}")
            print(f"  Days: {len(itinerary.day_plans)}")

            for day_plan in itinerary.day_plans:
                print(f"\n  Day {day_plan.day_number} ({day_plan.date}):")
                for activity in day_plan.activities:
                    print(f"    - {activity.name}: {activity.description}")
                    if activity.location:
                        print(f"      Location: {activity.location.address}")
        else:
            print("\nNo itinerary generated")

        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_workflow())
