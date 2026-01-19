"""
gRPC client test script

For quick testing of itinerary service gRPC interfaces
"""

import asyncio

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc


async def test_create_itinerary():
    """Test create itinerary"""
    print("=" * 60)
    print("Test 1: Create Itinerary")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        # Build itinerary data
        itinerary = itinerary_pb2.Itinerary(
            title="Shanghai 3-Day Trip",
            user_id="user_test_001",
            destination="Shanghai",
            start_date="2024-05-01",
            end_date="2024-05-03",
            interests=["culture", "food", "shopping"],
            budget_level=itinerary_pb2.BUDGET_LEVEL_MODERATE,
            num_travelers=2,
        )

        request = itinerary_pb2.CreateItineraryRequest(itinerary=itinerary)

        try:
            response = await stub.CreateItinerary(request)
            print("✅ Successfully created itinerary!")
            print(f"   Itinerary ID: {response.itinerary_id}")
            print(f"   Title: {response.itinerary.title}")
            print(f"   Destination: {response.itinerary.destination}")
            return response.itinerary_id
        except grpc.RpcError as e:
            print(f"❌ Creation failed: {e.details()}")
            return None


async def test_get_itinerary(itinerary_id: str):
    """Test get itinerary"""
    print("\n" + "=" * 60)
    print("Test 2: Get Itinerary")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        request = itinerary_pb2.GetItineraryRequest(itinerary_id=itinerary_id)

        try:
            response = await stub.GetItinerary(request)
            print("✅ Successfully retrieved itinerary!")
            print(f"   Title: {response.itinerary.title}")
            print(f"   Destination: {response.itinerary.destination}")
            print(
                f"   Dates: {response.itinerary.start_date} - "
                f"{response.itinerary.end_date}"
            )
            print(f"   Number of Travelers: {response.itinerary.num_travelers}")
            return response.itinerary
        except grpc.RpcError as e:
            print(f"❌ Retrieval failed: {e.details()}")
            return None


async def test_add_day_plan(itinerary_id: str):
    """Test add day plan"""
    print("\n" + "=" * 60)
    print("Test 3: Add Day Plan")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        day_plan = itinerary_pb2.DayPlan(
            day_number=1,
            date="2024-05-01",
            title="Day 1 - Arrive in Shanghai",
            notes="Check in to hotel, settle in",
        )

        request = itinerary_pb2.AddDayPlanRequest(
            itinerary_id=itinerary_id, day_plan=day_plan
        )

        try:
            response = await stub.AddDayPlan(request)
            print("✅ Successfully added day plan!")
            print(f"   Plan ID: {response.day_plan_id}")
            print(f"   Title: {response.day_plan.title}")
            return response.day_plan_id
        except grpc.RpcError as e:
            print(f"❌ Addition failed: {e.details()}")
            return None


async def test_add_activity(itinerary_id: str, day_plan_id: str):
    """Test add activity"""
    print("\n" + "=" * 60)
    print("Test 4: Add Activity")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        activity = itinerary_pb2.Activity(
            kind="attraction_visit",
            name="Visit The Bund",
            description="Explore Shanghai's iconic waterfront area",
            start_time="09:00",
            end_time="12:00",
            location=itinerary_pb2.Location(
                name="The Bund",
                latitude=31.2400,
                longitude=121.4900,
                address="Zhongshan East 1st Road, Huangpu District, Shanghai",
            ),
            category="sightseeing",
            cost=itinerary_pb2.Cost(amount=0, currency="CNY"),
        )

        request = itinerary_pb2.AddActivityRequest(
            itinerary_id=itinerary_id, day_plan_id=day_plan_id, activity=activity
        )

        try:
            response = await stub.AddActivity(request)
            print("✅ Successfully added activity!")
            print(f"   Activity ID: {response.activity_id}")
            print(f"   Activity Name: {response.activity.name}")
            print(
                f"   Time: {response.activity.start_time} - "
                f"{response.activity.end_time}"
            )
            return response.activity_id
        except grpc.RpcError as e:
            print(f"❌ Addition failed: {e.details()}")
            return None


async def test_list_user_itineraries(user_id: str):
    """Test list user itineraries"""
    print("\n" + "=" * 60)
    print("Test 5: List User Itineraries")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        request = itinerary_pb2.ListUserItinerariesRequest(
            user_id=user_id, page_number=0, page_size=10
        )

        try:
            response = await stub.ListUserItineraries(request)
            print("✅ Successfully retrieved itinerary list!")
            print(f"   Total Count: {response.total_count}")
            print(f"   Current Page: {response.page_number + 1}")
            print("   Itinerary List:")
            for i, itin in enumerate(response.itineraries, 1):
                print(f"     {i}. {itin.title} ({itin.destination})")
        except grpc.RpcError as e:
            print(f"❌ Retrieval failed: {e.details()}")


async def test_update_itinerary(itinerary_id: str):
    """Test update itinerary"""
    print("\n" + "=" * 60)
    print("Test 6: Update Itinerary")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        # First get the itinerary
        get_request = itinerary_pb2.GetItineraryRequest(itinerary_id=itinerary_id)
        get_response = await stub.GetItinerary(get_request)
        itinerary = get_response.itinerary

        # Modify data
        itinerary.title = "Shanghai 3-Day Trip (Updated)"
        itinerary.num_travelers = 4

        update_request = itinerary_pb2.UpdateItineraryRequest(itinerary=itinerary)

        try:
            response = await stub.UpdateItinerary(update_request)
            print("✅ Successfully updated itinerary!")
            print(f"   New Title: {response.itinerary.title}")
            print(f"   New Number of Travelers: {response.itinerary.num_travelers}")
        except grpc.RpcError as e:
            print(f"❌ Update failed: {e.details()}")


async def test_delete_itinerary(itinerary_id: str):
    """Test delete itinerary"""
    print("\n" + "=" * 60)
    print("Test 7: Delete Itinerary")
    print("=" * 60)

    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)

        request = itinerary_pb2.DeleteItineraryRequest(itinerary_id=itinerary_id)

        try:
            response = await stub.DeleteItinerary(request)
            if response.success:
                print("✅ Successfully deleted itinerary!")
            else:
                print("⚠️  Deletion failed (itinerary not found)")
        except grpc.RpcError as e:
            print(f"❌ Deletion failed: {e.details()}")


async def main():
    """Main test workflow"""
    print("\n" + "🚀 " * 20)
    print("trip-itinerary-service gRPC Interface Tests")
    print("🚀 " * 20 + "\n")

    # Test 1: Create itinerary
    itinerary_id = await test_create_itinerary()
    if not itinerary_id:
        print("\n❌ Failed to create itinerary, aborting tests")
        return

    # Test 2: Get itinerary
    await test_get_itinerary(itinerary_id)

    # Test 3: Add day plan
    day_plan_id = await test_add_day_plan(itinerary_id)
    if not day_plan_id:
        print("\n⚠️  Failed to add day plan, skipping activity test")
    else:
        # Test 4: Add activity
        await test_add_activity(itinerary_id, day_plan_id)

    # Test 5: List user itineraries
    await test_list_user_itineraries("user_test_001")

    # Test 6: Update itinerary
    await test_update_itinerary(itinerary_id)

    # Test 7: Delete itinerary
    await test_delete_itinerary(itinerary_id)

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
