"""Load generated protobuf modules used by the mixed Locust workload."""

from pathlib import Path
import sys


PROTO_ROOT = Path(__file__).resolve().parent / "proto"
if str(PROTO_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTO_ROOT))

from tripsphere.attraction.v1 import attraction_pb2, attraction_pb2_grpc
from tripsphere.common.v1 import date_pb2, map_pb2
from tripsphere.hotel.v1 import hotel_pb2, hotel_pb2_grpc
from tripsphere.itinerary.v1 import itinerary_pb2, itinerary_pb2_grpc
from tripsphere.product.v1 import product_pb2, product_pb2_grpc
from tripsphere.order.v1 import order_pb2, order_pb2_grpc, types_pb2

__all__ = [
    "attraction_pb2",
    "attraction_pb2_grpc",
    "date_pb2",
    "map_pb2",
    "hotel_pb2",
    "hotel_pb2_grpc",
    "itinerary_pb2",
    "itinerary_pb2_grpc",
    "product_pb2",
    "product_pb2_grpc",
    "order_pb2",
    "order_pb2_grpc",
    "types_pb2",
]
