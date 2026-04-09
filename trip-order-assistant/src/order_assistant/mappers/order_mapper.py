from typing import Any

from tripsphere.order.v1 import types_pb2


def contact_info_to_proto(contact_info: dict[str, Any]) -> types_pb2.ContactInfo:
    return types_pb2.ContactInfo(
        name=contact_info.get("name", ""),
        phone=contact_info.get("phone", ""),
        email=contact_info.get("email", ""),
    )


def order_source_to_proto(source: dict[str, Any]) -> types_pb2.OrderSource:
    return types_pb2.OrderSource(
        channel=source.get("channel", ""),
        agent_id=source.get("agent_id", ""),
        session_id=source.get("session_id", ""),
    )
