from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request

from itinerary_planner.grpc.clients.itinerary import ItineraryServiceClient
from itinerary_planner.nacos.naming import NacosNaming


def provide_nacos_naming(request: Request) -> NacosNaming:
    return cast(NacosNaming, request.app.state.nacos_naming)


def provide_itinerary_service_client(request: Request) -> ItineraryServiceClient:
    return cast(ItineraryServiceClient, request.app.state.itinerary_service_client)


def provide_current_user_id(request: Request) -> str:
    """Extract and validate the authenticated user ID from the x-user-id header.

    The Next.js proxy middleware strips client-supplied headers and injects a
    verified x-user-id from the RS256 JWT before forwarding requests, so this
    header is trusted on the internal network.
    """
    user_id = request.headers.get("x-user-id", "").strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return user_id


# Convenient annotated types for injection
CurrentUserId = Annotated[str, Depends(provide_current_user_id)]
ItineraryServiceClientDep = Annotated[
    ItineraryServiceClient, Depends(provide_itinerary_service_client)
]
