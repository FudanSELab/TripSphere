from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from itinerary.itinerary.models import Activity, DayPlan, Itinerary


class ItineraryRepository(ABC):
    """Itinerary repository abstract base class"""

    @abstractmethod
    async def create(self, itinerary: Itinerary) -> Itinerary: ...

    @abstractmethod
    async def find_by_id(self, itinerary_id: str) -> Itinerary | None: ...

    @abstractmethod
    async def update(self, itinerary: Itinerary) -> Itinerary | None: ...

    @abstractmethod
    async def delete_by_id(self, itinerary_id: str) -> bool: ...

    @abstractmethod
    async def find_by_user_id(
        self, user_id: str, page_number: int = 0, page_size: int = 10
    ) -> tuple[list[Itinerary], int]: ...

    @abstractmethod
    async def add_day_plan(
        self, itinerary_id: str, day_plan: DayPlan
    ) -> DayPlan | None: ...

    @abstractmethod
    async def update_day_plan(
        self, itinerary_id: str, day_plan: DayPlan
    ) -> DayPlan | None: ...

    @abstractmethod
    async def delete_day_plan(self, itinerary_id: str, day_plan_id: str) -> bool: ...

    @abstractmethod
    async def add_activity(
        self, itinerary_id: str, day_plan_id: str, activity: Activity
    ) -> Activity | None: ...

    @abstractmethod
    async def update_activity(
        self, itinerary_id: str, day_plan_id: str, activity: Activity
    ) -> Activity | None: ...

    @abstractmethod
    async def delete_activity(
        self, itinerary_id: str, day_plan_id: str, activity_id: str
    ) -> bool: ...

    @abstractmethod
    async def reorder_activities(
        self, itinerary_id: str, day_plan_id: str, activity_ids: list[str]
    ) -> DayPlan | None: ...


class MongoItineraryRepository(ItineraryRepository):
    """MongoDB itinerary repository implementation"""

    COLLECTION_NAME = "itineraries"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def create(self, itinerary: Itinerary) -> Itinerary:
        """Create a new itinerary"""
        document = itinerary.model_dump(by_alias=True, mode="json")
        await self.collection.insert_one(document)
        return itinerary

    async def find_by_id(self, itinerary_id: str) -> Itinerary | None:
        """Find itinerary by ID"""
        document = await self.collection.find_one({"_id": itinerary_id})
        if document is not None:
            return Itinerary.model_validate(document)
        return None

    async def update(self, itinerary: Itinerary) -> Itinerary | None:
        """Update itinerary"""
        itinerary.updated_at = datetime.now()
        document = itinerary.model_dump(by_alias=True, mode="json")

        result = await self.collection.replace_one({"_id": document["_id"]}, document)

        if result.modified_count > 0:
            return itinerary
        return None

    async def delete_by_id(self, itinerary_id: str) -> bool:
        """Delete itinerary by ID"""
        result = await self.collection.delete_one({"_id": itinerary_id})
        return result.deleted_count > 0

    async def find_by_user_id(
        self, user_id: str, page_number: int = 0, page_size: int = 10
    ) -> tuple[list[Itinerary], int]:
        """Find itinerary list by user ID (paginated)"""
        # Calculate total count
        total_count = await self.collection.count_documents({"user_id": user_id})

        # Paginated query
        skip = page_number * page_size
        cursor = (
            self.collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        documents = await cursor.to_list(length=page_size)
        itineraries = [Itinerary.model_validate(doc) for doc in documents]

        return itineraries, total_count

    async def add_day_plan(
        self, itinerary_id: str, day_plan: DayPlan
    ) -> DayPlan | None:
        """Add day plan"""
        day_plan_dict = day_plan.model_dump(by_alias=True, mode="json")

        result = await self.collection.update_one(
            {"_id": itinerary_id},
            {
                "$push": {"day_plans": day_plan_dict},
                "$set": {"updated_at": datetime.now()},
            },
        )

        if result.modified_count > 0:
            return day_plan
        return None

    async def update_day_plan(
        self, itinerary_id: str, day_plan: DayPlan
    ) -> DayPlan | None:
        """Update day plan"""
        day_plan_dict = day_plan.model_dump(by_alias=True, mode="json")

        result = await self.collection.update_one(
            {
                "_id": itinerary_id,
                "day_plans._id": day_plan.day_plan_id,
            },
            {
                "$set": {
                    "day_plans.$": day_plan_dict,
                    "updated_at": datetime.now(),
                }
            },
        )

        if result.modified_count > 0:
            return day_plan
        return None

    async def delete_day_plan(self, itinerary_id: str, day_plan_id: str) -> bool:
        """Delete day plan"""
        result = await self.collection.update_one(
            {"_id": itinerary_id},
            {
                "$pull": {"day_plans": {"_id": day_plan_id}},
                "$set": {"updated_at": datetime.now()},
            },
        )

        return result.modified_count > 0

    async def add_activity(
        self, itinerary_id: str, day_plan_id: str, activity: Activity
    ) -> Activity | None:
        """Add activity to specified day plan"""
        activity_dict = activity.model_dump(by_alias=True, mode="json")

        result = await self.collection.update_one(
            {
                "_id": itinerary_id,
                "day_plans._id": day_plan_id,
            },
            {
                "$push": {"day_plans.$.activities": activity_dict},
                "$set": {"updated_at": datetime.now()},
            },
        )

        if result.modified_count > 0:
            return activity
        return None

    async def update_activity(
        self, itinerary_id: str, day_plan_id: str, activity: Activity
    ) -> Activity | None:
        """Update activity"""
        activity_dict = activity.model_dump(by_alias=True, mode="json")

        result = await self.collection.update_one(
            {
                "_id": itinerary_id,
                "day_plans._id": day_plan_id,
                "day_plans.activities._id": activity.activity_id,
            },
            {
                "$set": {
                    "day_plans.$[dayPlan].activities.$[activity]": activity_dict,
                    "updated_at": datetime.now(),
                }
            },
            array_filters=[
                {"dayPlan._id": day_plan_id},
                {"activity._id": activity.activity_id},
            ],
        )

        if result.modified_count > 0:
            return activity
        return None

    async def delete_activity(
        self, itinerary_id: str, day_plan_id: str, activity_id: str
    ) -> bool:
        """Delete activity"""
        result = await self.collection.update_one(
            {
                "_id": itinerary_id,
                "day_plans._id": day_plan_id,
            },
            {
                "$pull": {"day_plans.$.activities": {"_id": activity_id}},
                "$set": {"updated_at": datetime.now()},
            },
        )

        return result.modified_count > 0

    async def reorder_activities(
        self, itinerary_id: str, day_plan_id: str, activity_ids: list[str]
    ) -> DayPlan | None:
        """Reorder activities"""
        # First get the itinerary
        itinerary = await self.find_by_id(itinerary_id)
        if not itinerary:
            return None

        # Find the corresponding day_plan
        day_plan_to_update = None
        for day_plan in itinerary.day_plans:
            if day_plan.day_plan_id == day_plan_id:
                day_plan_to_update = day_plan
                break

        if not day_plan_to_update:
            return None

        # Create activity ID to activity mapping
        activity_map = {
            activity.activity_id: activity for activity in day_plan_to_update.activities
        }

        # Reorder activities according to new order
        reordered_activities: list[Activity] = []
        for activity_id in activity_ids:
            if activity_id in activity_map:
                reordered_activities.append(activity_map[activity_id])

        # Update day_plan's activity list
        day_plan_to_update.activities = reordered_activities

        # Save updated day_plan
        updated_day_plan = await self.update_day_plan(itinerary_id, day_plan_to_update)
        return updated_day_plan
