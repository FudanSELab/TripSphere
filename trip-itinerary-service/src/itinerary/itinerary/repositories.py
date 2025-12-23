from abc import ABC, abstractmethod
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from itinerary.itinerary.models import Itinerary


class ItineraryRepository(ABC):
    @abstractmethod
    async def create(self, itinerary: Itinerary) -> None: ...

    @abstractmethod
    async def find_by_id(self, itinerary_id: str) -> Itinerary | None: ...

    @abstractmethod
    async def delete_by_id(self, itinerary_id: str) -> None: ...


class MongoItineraryRepositories:
    COLLECTION_NAME = "itineraries"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def create(self, itinerary: Itinerary) -> None:
        document = itinerary.model_dump(by_alias=True)
        await self.collection.replace_one(
            {"_id": document["_id"]}, document, upsert=True
        )

    async def find_by_id(self, itinerary_id: str) -> Itinerary | None:
        document = await self.collection.find_one({"_id": itinerary_id})
        if document is not None:
            return Itinerary.model_validate(document)
        return None

    async def delete_by_id(self, itinerary_id: str) -> None:
        await self.collection.delete_one({"_id": itinerary_id})
