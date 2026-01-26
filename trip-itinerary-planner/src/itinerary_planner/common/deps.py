from typing import cast

from fastapi import Request

from itinerary_planner.nacos.naming import NacosNaming


def provide_nacos_naming(request: Request) -> NacosNaming:
    return cast(NacosNaming, request.app.state.nacos_naming)
