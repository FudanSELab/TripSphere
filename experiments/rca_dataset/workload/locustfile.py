"""Mixed, steady TripSphere workload used during every fault window."""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import date, timedelta
from typing import Any, Callable

import grpc
from locust import HttpUser, User, constant_pacing, task

from workload_config import (
    ATTRACTION_IDS,
    ATTRACTION_REQUEST_WEIGHTS,
    CHAT_PROMPTS,
    DEFAULT_ORDER_SKU_ID,
    HOTEL_IDS,
    HOTEL_REQUEST_WEIGHTS,
    ORDER_MAX_DAYS_AHEAD_ENV,
    ORDER_MIN_DAYS_AHEAD_ENV,
    ORDER_SKU_IDS,
    ORDER_FLOW_WEIGHTS,
    PLANNER_SCENARIOS,
    PRODUCT_RESOURCE_IDS,
    RATES,
    REVIEW_SUMMARY_QUERIES,
    TEST_CITIES,
    TRAFFIC_USER_IDS,
)
from workload_proto import (
    attraction_pb2,
    attraction_pb2_grpc,
    date_pb2,
    hotel_pb2,
    hotel_pb2_grpc,
    itinerary_pb2,
    itinerary_pb2_grpc,
    map_pb2,
    order_pb2,
    order_pb2_grpc,
    product_pb2,
    product_pb2_grpc,
    types_pb2,
)

def env_value(name: str, legacy_name: str, default: str) -> str:
    return os.getenv(name) or os.getenv(legacy_name) or default


def grpc_call(
    user: User,
    name: str,
    call: Callable[..., Any],
    request: Any,
    metadata: tuple[tuple[str, str], ...],
) -> Any:
    started = time.perf_counter()
    try:
        response = call(
            request,
            metadata=metadata,
            timeout=float(env_value(
                "TRIPSPHERE_RCA_GRPC_TIMEOUT_SECONDS",
                "CPU_HOG_GRPC_TIMEOUT_SECONDS",
                "30",
            )),
        )
    except grpc.RpcError as exc:
        user.environment.events.request.fire(
            request_type="gRPC",
            name=name,
            response_time=(time.perf_counter() - started) * 1000,
            response_length=0,
            exception=exc,
        )
        return None
    user.environment.events.request.fire(
        request_type="gRPC",
        name=name,
        response_time=(time.perf_counter() - started) * 1000,
        response_length=response.ByteSize(),
        exception=None,
    )
    return response


class RateLimitedHttpUser(HttpUser):
    abstract = True
    wait_time = constant_pacing(1)

    def on_start(self) -> None:
        self.user_id = random.choice(TRAFFIC_USER_IDS)


class RateLimitedGrpcUser(User):
    abstract = True
    wait_time = constant_pacing(1)

    def on_start(self) -> None:
        self.user_id = random.choice(TRAFFIC_USER_IDS)


class PlannerUser(RateLimitedHttpUser):
    rate = RATES["planner"]
    host = env_value("TRIPSPHERE_RCA_PLANNER_HOST", "CPU_HOG_PLANNER_HOST", "http://localhost:24215")
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    @task
    def plan_itinerary(self) -> None:
        scenario = random.choice(PLANNER_SCENARIOS)
        start = date.today() + timedelta(days=random.randint(7, 30))
        end = start + timedelta(days=scenario["days"] - 1)
        request_id = uuid.uuid4().hex
        path = (
            "/api/v1/itineraries/plannings/stream"
            if env_value("TRIPSPHERE_RCA_PLANNER_SSE", "CPU_HOG_PLANNER_SSE", "0") == "1"
            else "/api/v1/itineraries/plannings"
        )
        payload = {
            "destination": scenario["destination"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "interests": scenario["interests"],
            "pace": scenario["pace"],
            "additional_preferences": scenario["preferences"],
        }
        with self.client.post(
            path,
            data=json.dumps(payload),
            headers={
                "content-type": "application/json",
                "x-user-id": self.user_id,
            },
            name="planner itinerary planning",
            catch_response=True,
        ) as response:
            if not response.ok:
                response.failure(f"HTTP {response.status_code}")
            elif env_value("TRIPSPHERE_RCA_PLANNER_SSE", "CPU_HOG_PLANNER_SSE", "0") == "1" and "event: failed" in response.text:
                response.failure("SSE planning failed")


class ChatUser(RateLimitedHttpUser):
    rate = RATES["chat"]
    host = env_value("TRIPSPHERE_RCA_CHAT_HOST", "CPU_HOG_CHAT_HOST", "http://localhost:24210")
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    @task
    def chat(self) -> None:
        request_id = uuid.uuid4().hex
        payload = {
            "threadId": f"traffic-chat-{request_id}",
            "runId": f"traffic-chat-run-{request_id}",
            "state": {"headers": {"user_id": self.user_id}},
            "messages": [{
                "id": f"msg-{request_id}",
                "role": "user",
                "content": random.choice(CHAT_PROMPTS),
            }],
            "tools": [],
            "context": [],
            "forwardedProps": {},
        }
        with self.client.post(
            "/",
            data=json.dumps(payload),
            headers={"content-type": "application/json", "accept": "text/event-stream"},
            name="chat assistant",
            catch_response=True,
        ) as response:
            if not response.ok:
                response.failure(f"HTTP {response.status_code}")


class ReviewSummaryUser(RateLimitedHttpUser):
    rate = RATES["review_summary"]
    host = env_value(
        "TRIPSPHERE_RCA_REVIEW_SUMMARY_HOST",
        "CPU_HOG_REVIEW_SUMMARY_HOST",
        "http://localhost:24212",
    )
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    @task
    def summarize_reviews(self) -> None:
        target_type = random.choice(("attraction", "hotel"))
        target_id = random.choice(
            ATTRACTION_IDS if target_type == "attraction" else HOTEL_IDS
        )
        with self.client.post(
            "/api/v1/review-summaries",
            json={"query": random.choice(REVIEW_SUMMARY_QUERIES)},
            headers={
                "x-review-target-id": target_id,
                "x-review-target-type": target_type,
            },
            name="review summary",
            catch_response=True,
        ) as response:
            if not response.ok:
                response.failure(f"HTTP {response.status_code}")


class OrderUser(RateLimitedGrpcUser):
    rate = RATES["order"]
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    def on_start(self) -> None:
        super().on_start()
        self.fixed_sku_id = os.getenv(
            "TRIPSPHERE_RCA_ORDER_SKU_ID"
        ) or os.getenv("CPU_HOG_ORDER_SKU_ID")
        self.fixed_order_date = (
            env_value(
                "TRIPSPHERE_RCA_ORDER_DATE",
                "CPU_HOG_ORDER_DATE",
                "",
            )
            or None
        )
        self.min_days_ahead = int(os.getenv(ORDER_MIN_DAYS_AHEAD_ENV, "7"))
        self.max_days_ahead = int(os.getenv(ORDER_MAX_DAYS_AHEAD_ENV, "30"))
        if self.min_days_ahead < 1 or self.max_days_ahead < self.min_days_ahead:
            raise ValueError(
                "order date window must satisfy 1 <= min_days_ahead <= max_days_ahead"
            )
        self.channel_args = (("x-user-id", self.user_id),)
        self.channel = grpc.insecure_channel(
            env_value("TRIPSPHERE_RCA_ORDER_HOST", "CPU_HOG_ORDER_HOST", "localhost:50062")
        )
        self.stub = order_pb2_grpc.OrderServiceStub(self.channel)

    def on_stop(self) -> None:
        self.channel.close()

    def create_order(self) -> str | None:
        request_id = uuid.uuid4().hex
        sku_id, order_date = self._choose_order()
        checkout_date = order_date + timedelta(days=1)
        response = grpc_call(
            self,
            "OrderService/CreateOrder",
            self.stub.CreateOrder,
            order_pb2.CreateOrderRequest(
                user_id=self.user_id,
                request_id=request_id,
                items=[order_pb2.CreateOrderItem(
                    sku_id=sku_id,
                    date=date_pb2.Date(
                        year=order_date.year,
                        month=order_date.month,
                        day=order_date.day,
                    ),
                    end_date=date_pb2.Date(
                        year=checkout_date.year,
                        month=checkout_date.month,
                        day=checkout_date.day,
                    ),
                    quantity=1,
                )],
                contact=types_pb2.ContactInfo(
                    name="TripSphere Traffic",
                    phone="13800000000",
                    email="traffic@example.invalid",
                ),
                source=types_pb2.OrderSource(
                    channel="mixed-traffic",
                    session_id=f"traffic-order-{request_id}",
                ),
            ),
            self.channel_args,
        )
        return response.order.id if response and response.HasField("order") else None

    def _choose_order(self) -> tuple[str, date]:
        sku_id = self.fixed_sku_id or random.choice(ORDER_SKU_IDS)
        if self.fixed_order_date:
            order_date = date.fromisoformat(self.fixed_order_date)
        else:
            order_date = date.today() + timedelta(
                days=random.randint(self.min_days_ahead, self.max_days_ahead)
            )
        return sku_id or DEFAULT_ORDER_SKU_ID, order_date

    @task
    def order_flow(self) -> None:
        flow = random.choices(
            tuple(ORDER_FLOW_WEIGHTS),
            weights=tuple(ORDER_FLOW_WEIGHTS.values()),
        )[0]
        order_id = self.create_order()
        if not order_id:
            return
        if flow == "create_then_cancel":
            grpc_call(
                self,
                "OrderService/CancelOrder",
                self.stub.CancelOrder,
                order_pb2.CancelOrderRequest(
                    order_id=order_id, reason="normal traffic cancellation"
                ),
                self.channel_args,
            )
        elif flow == "create_then_pay":
            grpc_call(
                self,
                "OrderService/ConfirmPayment",
                self.stub.ConfirmPayment,
                order_pb2.ConfirmPaymentRequest(
                    order_id=order_id, payment_method="mock"
                ),
                self.channel_args,
            )


class AttractionUser(RateLimitedGrpcUser):
    rate = RATES["attraction"]
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    def on_start(self) -> None:
        super().on_start()
        self.attraction_ids = list(ATTRACTION_IDS)
        self.channel = grpc.insecure_channel(
            env_value("TRIPSPHERE_RCA_ATTRACTION_HOST", "CPU_HOG_ATTRACTION_HOST", "localhost:50053")
        )
        self.stub = attraction_pb2_grpc.AttractionServiceStub(self.channel)

    def on_stop(self) -> None:
        self.channel.close()

    @task
    def browse(self) -> None:
        request_name = random.choices(
            tuple(ATTRACTION_REQUEST_WEIGHTS),
            weights=tuple(ATTRACTION_REQUEST_WEIGHTS.values()),
        )[0]
        if request_name == "list_by_city":
            request = attraction_pb2.ListAttractionsByCityRequest(
                city=random.choice(TEST_CITIES), page_size=10
            )
            response = grpc_call(
                self, "AttractionService/ListAttractionsByCity",
                self.stub.ListAttractionsByCity, request, (),
            )
            if response:
                self.attraction_ids.extend(
                    item.id for item in response.attractions if item.id
                )
        elif request_name == "get_by_id":
            grpc_call(
                self, "AttractionService/GetAttractionById",
                self.stub.GetAttractionById,
                attraction_pb2.GetAttractionByIdRequest(
                    id=random.choice(self.attraction_ids)
                ),
                (),
            )
        else:
            grpc_call(
                self, "AttractionService/GetAttractionsNearby",
                self.stub.GetAttractionsNearby,
                attraction_pb2.GetAttractionsNearbyRequest(
                    location=map_pb2.GeoPoint(longitude=121.50, latitude=31.23),
                    radius_meters=3000,
                ),
                (),
            )


class HotelUser(RateLimitedGrpcUser):
    rate = RATES["hotel"]
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    def on_start(self) -> None:
        super().on_start()
        self.hotel_ids = list(HOTEL_IDS)
        self.channel = grpc.insecure_channel(
            env_value("TRIPSPHERE_RCA_HOTEL_HOST", "CPU_HOG_HOTEL_HOST", "localhost:50054")
        )
        self.stub = hotel_pb2_grpc.HotelServiceStub(self.channel)

    def on_stop(self) -> None:
        self.channel.close()

    @task
    def browse(self) -> None:
        request_name = random.choices(
            tuple(HOTEL_REQUEST_WEIGHTS),
            weights=tuple(HOTEL_REQUEST_WEIGHTS.values()),
        )[0]
        if request_name == "list":
            response = grpc_call(
                self, "HotelService/ListHotels", self.stub.ListHotels,
                hotel_pb2.ListHotelsRequest(
                    city=random.choice(TEST_CITIES), page_size=10
                ), (),
            )
            if response:
                self.hotel_ids.extend(item.id for item in response.hotels if item.id)
        elif request_name == "get_by_id":
            grpc_call(
                self, "HotelService/GetHotelById", self.stub.GetHotelById,
                hotel_pb2.GetHotelByIdRequest(id=random.choice(self.hotel_ids)), (),
            )
        elif request_name == "rooms":
            grpc_call(
                self, "HotelService/GetRoomTypesByHotelId",
                self.stub.GetRoomTypesByHotelId,
                hotel_pb2.GetRoomTypesByHotelIdRequest(
                    hotel_id=random.choice(self.hotel_ids)
                ), (),
            )
        else:
            grpc_call(
                self, "HotelService/GetHotelsNearby", self.stub.GetHotelsNearby,
                hotel_pb2.GetHotelsNearbyRequest(
                    location=map_pb2.GeoPoint(longitude=121.50, latitude=31.23),
                    radius_meters=3000,
                ), (),
            )


class ProductUser(RateLimitedGrpcUser):
    rate = RATES["product"]
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    def on_start(self) -> None:
        super().on_start()
        self.channel = grpc.insecure_channel(
            env_value("TRIPSPHERE_RCA_PRODUCT_HOST", "CPU_HOG_PRODUCT_HOST", "localhost:50060")
        )
        self.stub = product_pb2_grpc.ProductServiceStub(self.channel)

    def on_stop(self) -> None:
        self.channel.close()

    @task
    def browse(self) -> None:
        grpc_call(
            self, "ProductService/ListSpusByResource",
            self.stub.ListSpusByResource,
            product_pb2.ListSpusByResourceRequest(
                resource_type=product_pb2.RESOURCE_TYPE_HOTEL_ROOM,
                resource_id=random.choice(PRODUCT_RESOURCE_IDS),
                page_size=10,
            ), (),
        )


class ItineraryUser(RateLimitedGrpcUser):
    rate = RATES["itinerary"]
    fixed_count = rate.users
    wait_time = constant_pacing(rate.users / rate.requests_per_second)

    def on_start(self) -> None:
        super().on_start()
        self.channel = grpc.insecure_channel(
            env_value("TRIPSPHERE_RCA_ITINERARY_HOST", "CPU_HOG_ITINERARY_HOST", "localhost:50052")
        )
        self.stub = itinerary_pb2_grpc.ItineraryServiceStub(self.channel)

    def on_stop(self) -> None:
        self.channel.close()

    @task
    def list_itineraries(self) -> None:
        grpc_call(
            self, "ItineraryService/ListUserItineraries",
            self.stub.ListUserItineraries,
            itinerary_pb2.ListUserItinerariesRequest(
                user_id=self.user_id, page_size=10
            ), (("x-user-id", self.user_id),),
        )
