import logging
from datetime import date, datetime

import grpc
from tripsphere.itinerary import itinerary_pb2, itinerary_pb2_grpc

from itinerary.itinerary.models import (
    Activity,
    ActivityLocation,
    BudgetLevel,
    Coordinates,
    Cost,
    DayPlan,
    Itinerary,
    ItinerarySummary,
)
from itinerary.itinerary.repositories import ItineraryRepository

logger = logging.getLogger(__name__)


class ItineraryServiceServicer(itinerary_pb2_grpc.ItineraryServiceServicer):
    def __init__(self, repository: ItineraryRepository) -> None:
        self.repository = repository

    async def CreateItinerary(
        self,
        request: itinerary_pb2.CreateItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.CreateItineraryRequest, itinerary_pb2.CreateItineraryResponse
        ],
    ) -> itinerary_pb2.CreateItineraryResponse:
        try:
            # Convert proto to model
            itinerary = self._proto_to_itinerary(request.itinerary)

            # Save to database
            created = await self.repository.create(itinerary)

            logger.info(f"Created itinerary: {created.itinerary_id}")

            # Convert back to proto
            itinerary_proto = self._itinerary_to_proto(created)

            return itinerary_pb2.CreateItineraryResponse(
                itinerary_id=created.itinerary_id, itinerary=itinerary_proto
            )

        except Exception as e:
            logger.error(f"Failed to create itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to create itinerary: {str(e)}"
            )

    async def GetItinerary(
        self,
        request: itinerary_pb2.GetItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.GetItineraryRequest, itinerary_pb2.GetItineraryResponse
        ],
    ) -> itinerary_pb2.GetItineraryResponse:
        try:
            itinerary = await self.repository.find_by_id(request.itinerary_id)

            if not itinerary:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Itinerary not found: {request.itinerary_id}",
                )

            itinerary_proto = self._itinerary_to_proto(itinerary)

            return itinerary_pb2.GetItineraryResponse(itinerary=itinerary_proto)

        except Exception as e:
            logger.error(f"Failed to get itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to get itinerary: {str(e)}"
            )

    async def UpdateItinerary(
        self,
        request: itinerary_pb2.UpdateItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.UpdateItineraryRequest, itinerary_pb2.UpdateItineraryResponse
        ],
    ) -> itinerary_pb2.UpdateItineraryResponse:
        try:
            itinerary = self._proto_to_itinerary(request.itinerary)
            updated = await self.repository.update(itinerary)

            if not updated:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Itinerary not found: {itinerary.itinerary_id}",
                )

            itinerary_proto = self._itinerary_to_proto(updated)

            return itinerary_pb2.UpdateItineraryResponse(itinerary=itinerary_proto)

        except Exception as e:
            logger.error(f"Failed to update itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to update itinerary: {str(e)}"
            )

    async def DeleteItinerary(
        self,
        request: itinerary_pb2.DeleteItineraryRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.DeleteItineraryRequest, itinerary_pb2.DeleteItineraryResponse
        ],
    ) -> itinerary_pb2.DeleteItineraryResponse:
        try:
            success = await self.repository.delete_by_id(request.itinerary_id)

            return itinerary_pb2.DeleteItineraryResponse(success=success)

        except Exception as e:
            logger.error(f"Failed to delete itinerary: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to delete itinerary: {str(e)}"
            )

    async def ListUserItineraries(
        self,
        request: itinerary_pb2.ListUserItinerariesRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.ListUserItinerariesRequest,
            itinerary_pb2.ListUserItinerariesResponse,
        ],
    ) -> itinerary_pb2.ListUserItinerariesResponse:
        try:
            itineraries, total_count = await self.repository.find_by_user_id(
                user_id=request.user_id,
                page_number=request.page_number,
                page_size=request.page_size,
            )

            itinerary_protos = [self._itinerary_to_proto(it) for it in itineraries]

            return itinerary_pb2.ListUserItinerariesResponse(
                itineraries=itinerary_protos,
                total_count=total_count,
                page_number=request.page_number,
                page_size=request.page_size,
            )

        except Exception as e:
            logger.error(f"Failed to list user itineraries: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to list itineraries: {str(e)}"
            )

    async def AddDayPlan(
        self,
        request: itinerary_pb2.AddDayPlanRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.AddDayPlanRequest, itinerary_pb2.AddDayPlanResponse
        ],
    ) -> itinerary_pb2.AddDayPlanResponse:
        try:
            day_plan = self._proto_to_day_plan(request.day_plan)
            added = await self.repository.add_day_plan(request.itinerary_id, day_plan)

            if not added:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Itinerary not found: {request.itinerary_id}",
                )

            day_plan_proto = self._day_plan_to_proto(added)

            return itinerary_pb2.AddDayPlanResponse(
                day_plan_id=added.day_plan_id, day_plan=day_plan_proto
            )

        except Exception as e:
            logger.error(f"Failed to add day plan: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to add day plan: {str(e)}"
            )

    async def UpdateDayPlan(
        self,
        request: itinerary_pb2.UpdateDayPlanRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.UpdateDayPlanRequest, itinerary_pb2.UpdateDayPlanResponse
        ],
    ) -> itinerary_pb2.UpdateDayPlanResponse:
        try:
            day_plan = self._proto_to_day_plan(request.day_plan)
            updated = await self.repository.update_day_plan(
                request.itinerary_id, day_plan
            )

            if not updated:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"DayPlan not found in itinerary: {request.itinerary_id}",
                )

            day_plan_proto = self._day_plan_to_proto(updated)

            return itinerary_pb2.UpdateDayPlanResponse(day_plan=day_plan_proto)

        except Exception as e:
            logger.error(f"Failed to update day plan: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to update day plan: {str(e)}"
            )

    async def DeleteDayPlan(
        self,
        request: itinerary_pb2.DeleteDayPlanRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.DeleteDayPlanRequest, itinerary_pb2.DeleteDayPlanResponse
        ],
    ) -> itinerary_pb2.DeleteDayPlanResponse:
        try:
            success = await self.repository.delete_day_plan(
                request.itinerary_id, request.day_plan_id
            )

            return itinerary_pb2.DeleteDayPlanResponse(success=success)

        except Exception as e:
            logger.error(f"Failed to delete day plan: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to delete day plan: {str(e)}"
            )

    async def AddActivity(
        self,
        request: itinerary_pb2.AddActivityRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.AddActivityRequest, itinerary_pb2.AddActivityResponse
        ],
    ) -> itinerary_pb2.AddActivityResponse:
        try:
            activity = self._proto_to_activity(request.activity)
            added = await self.repository.add_activity(
                request.itinerary_id, request.day_plan_id, activity
            )

            if not added:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND, "Itinerary or DayPlan not found"
                )

            activity_proto = self._activity_to_proto(added)

            return itinerary_pb2.AddActivityResponse(
                activity_id=added.activity_id, activity=activity_proto
            )

        except Exception as e:
            logger.error(f"Failed to add activity: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to add activity: {str(e)}"
            )

    async def UpdateActivity(
        self,
        request: itinerary_pb2.UpdateActivityRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.UpdateActivityRequest, itinerary_pb2.UpdateActivityResponse
        ],
    ) -> itinerary_pb2.UpdateActivityResponse:
        try:
            activity = self._proto_to_activity(request.activity)
            updated = await self.repository.update_activity(
                request.itinerary_id, request.day_plan_id, activity
            )

            if not updated:
                await context.abort(grpc.StatusCode.NOT_FOUND, "Activity not found")

            activity_proto = self._activity_to_proto(updated)

            return itinerary_pb2.UpdateActivityResponse(activity=activity_proto)

        except Exception as e:
            logger.error(f"Failed to update activity: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to update activity: {str(e)}"
            )

    async def DeleteActivity(
        self,
        request: itinerary_pb2.DeleteActivityRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.DeleteActivityRequest, itinerary_pb2.DeleteActivityResponse
        ],
    ) -> itinerary_pb2.DeleteActivityResponse:
        try:
            success = await self.repository.delete_activity(
                request.itinerary_id, request.day_plan_id, request.activity_id
            )

            return itinerary_pb2.DeleteActivityResponse(success=success)

        except Exception as e:
            logger.error(f"Failed to delete activity: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to delete activity: {str(e)}"
            )

    async def ReorderActivities(
        self,
        request: itinerary_pb2.ReorderActivitiesRequest,
        context: grpc.aio.ServicerContext[
            itinerary_pb2.ReorderActivitiesRequest,
            itinerary_pb2.ReorderActivitiesResponse,
        ],
    ) -> itinerary_pb2.ReorderActivitiesResponse:
        try:
            day_plan = await self.repository.reorder_activities(
                request.itinerary_id, request.day_plan_id, list(request.activity_ids)
            )

            if not day_plan:
                await context.abort(grpc.StatusCode.NOT_FOUND, "DayPlan not found")

            day_plan_proto = self._day_plan_to_proto(day_plan)

            return itinerary_pb2.ReorderActivitiesResponse(day_plan=day_plan_proto)

        except Exception as e:
            logger.error(f"Failed to reorder activities: {e}", exc_info=True)
            await context.abort(
                grpc.StatusCode.INTERNAL, f"Failed to reorder activities: {str(e)}"
            )

    # ========== Helper conversion methods ==========

    def _proto_to_itinerary(self, proto: itinerary_pb2.Itinerary) -> Itinerary:
        """Convert proto to model"""
        return Itinerary(
            _id=proto.itinerary_id,
            title=proto.title,
            user_id=proto.user_id,
            destination=proto.destination,
            start_date=date.fromisoformat(proto.start_date),
            end_date=date.fromisoformat(proto.end_date),
            day_plans=[self._proto_to_day_plan(dp) for dp in proto.day_plans],
            summary=self._proto_to_summary(proto.summary)
            if proto.HasField("summary")
            else ItinerarySummary(),
            created_at=datetime.fromisoformat(proto.created_at)
            if proto.created_at
            else datetime.now(),
            updated_at=datetime.fromisoformat(proto.updated_at)
            if proto.updated_at
            else datetime.now(),
            interests=list[str](proto.interests),
            budget_level=self._proto_to_budget_level(proto.budget_level),
            num_travelers=proto.num_travelers,
            metadata=None,
        )

    def _itinerary_to_proto(self, itinerary: Itinerary) -> itinerary_pb2.Itinerary:
        """Convert model to proto"""
        return itinerary_pb2.Itinerary(
            itinerary_id=itinerary.itinerary_id,
            title=itinerary.title,
            user_id=itinerary.user_id,
            destination=itinerary.destination,
            start_date=itinerary.start_date.isoformat(),
            end_date=itinerary.end_date.isoformat(),
            day_plans=[self._day_plan_to_proto(dp) for dp in itinerary.day_plans],
            summary=self._summary_to_proto(itinerary.summary),
            created_at=itinerary.created_at.isoformat(),
            updated_at=itinerary.updated_at.isoformat(),
            interests=itinerary.interests,
            budget_level=self._budget_level_to_proto(itinerary.budget_level),
            num_travelers=itinerary.num_travelers,
        )

    def _proto_to_day_plan(self, proto: itinerary_pb2.DayPlan) -> DayPlan:
        """Convert proto to DayPlan"""
        return DayPlan(
            _id=proto.day_plan_id,
            day_number=proto.day_number,
            date=date.fromisoformat(proto.date) if proto.date else None,
            title=proto.title,
            activities=[self._proto_to_activity(act) for act in proto.activities],
            notes=proto.notes,
            metadata=None,
        )

    def _day_plan_to_proto(self, day_plan: DayPlan) -> itinerary_pb2.DayPlan:
        """Convert DayPlan to proto"""
        return itinerary_pb2.DayPlan(
            day_plan_id=day_plan.day_plan_id,
            day_number=day_plan.day_number,
            date=day_plan.date.isoformat() if day_plan.date else "",
            title=day_plan.title,
            activities=[self._activity_to_proto(act) for act in day_plan.activities],
            notes=day_plan.notes,
        )

    def _proto_to_activity(self, proto: itinerary_pb2.Activity) -> Activity:
        """Convert proto to Activity"""
        return Activity(
            _id=proto.activity_id,
            kind=proto.kind,
            name=proto.name,
            description=proto.description,
            start_time=proto.start_time,
            end_time=proto.end_time,
            location=self._proto_to_activity_location(proto.location)
            if proto.HasField("location")
            else ActivityLocation(),
            category=proto.category,
            cost=self._proto_to_cost(proto.cost) if proto.HasField("cost") else Cost(),
            attraction_id=proto.attraction_id or None,
            hotel_id=proto.hotel_id or None,
            metadata=None,
        )

    def _activity_to_proto(self, activity: Activity) -> itinerary_pb2.Activity:
        """Convert Activity to proto"""
        return itinerary_pb2.Activity(
            activity_id=activity.activity_id,
            kind=activity.kind,
            name=activity.name,
            description=activity.description,
            start_time=activity.start_time,
            end_time=activity.end_time,
            location=self._activity_location_to_proto(activity.location),
            category=activity.category,
            cost=self._cost_to_proto(activity.cost),
            attraction_id=activity.attraction_id or "",
            hotel_id=activity.hotel_id or "",
        )

    def _proto_to_activity_location(
        self, proto: itinerary_pb2.ActivityLocation
    ) -> ActivityLocation:
        """Convert proto to ActivityLocation"""

        coordinates = Coordinates(
            longitude=proto.coordinates.longitude
            if proto.HasField("coordinates")
            else 0.0,
            latitude=proto.coordinates.latitude
            if proto.HasField("coordinates")
            else 0.0,
        )

        return ActivityLocation(
            name=proto.name,
            coordinates=coordinates,
            address=proto.address,
        )

    def _activity_location_to_proto(
        self, location: ActivityLocation
    ) -> itinerary_pb2.ActivityLocation:
        """Convert ActivityLocation to proto"""
        from tripsphere.common import geo_pb2

        return itinerary_pb2.ActivityLocation(
            name=location.name,
            coordinates=geo_pb2.Location(
                longitude=location.coordinates.longitude,
                latitude=location.coordinates.latitude,
            ),
            address=location.address,
        )

    def _proto_to_cost(self, proto: itinerary_pb2.Cost) -> Cost:
        """Convert proto to Cost"""
        return Cost(amount=proto.amount, currency=proto.currency)

    def _cost_to_proto(self, cost: Cost) -> itinerary_pb2.Cost:
        """Convert Cost to proto"""
        return itinerary_pb2.Cost(amount=cost.amount, currency=cost.currency)

    def _proto_to_summary(
        self, proto: itinerary_pb2.ItinerarySummary
    ) -> ItinerarySummary:
        """Convert proto to ItinerarySummary"""
        return ItinerarySummary(
            total_estimated_cost=proto.total_estimated_cost,
            currency=proto.currency,
            total_activities=proto.total_activities,
            highlights=list(proto.highlights),
        )

    def _summary_to_proto(
        self, summary: ItinerarySummary
    ) -> itinerary_pb2.ItinerarySummary:
        """Convert ItinerarySummary to proto"""
        return itinerary_pb2.ItinerarySummary(
            total_estimated_cost=summary.total_estimated_cost,
            currency=summary.currency,
            total_activities=summary.total_activities,
            highlights=summary.highlights,
        )

    def _proto_to_budget_level(self, proto_enum: int) -> BudgetLevel:
        """Convert proto enum to BudgetLevel"""
        mapping = {
            0: BudgetLevel.UNSPECIFIED,
            1: BudgetLevel.BUDGET,
            2: BudgetLevel.MODERATE,
            3: BudgetLevel.LUXURY,
        }
        return mapping.get(proto_enum, BudgetLevel.MODERATE)

    def _budget_level_to_proto(
        self, budget_level: BudgetLevel
    ) -> itinerary_pb2.BudgetLevel.ValueType:
        """Convert BudgetLevel to proto enum"""
        mapping = {
            BudgetLevel.UNSPECIFIED: itinerary_pb2.BUDGET_LEVEL_UNSPECIFIED,
            BudgetLevel.BUDGET: itinerary_pb2.BUDGET_LEVEL_BUDGET,
            BudgetLevel.MODERATE: itinerary_pb2.BUDGET_LEVEL_MODERATE,
            BudgetLevel.LUXURY: itinerary_pb2.BUDGET_LEVEL_LUXURY,
        }
        return mapping.get(budget_level, itinerary_pb2.BUDGET_LEVEL_MODERATE)
