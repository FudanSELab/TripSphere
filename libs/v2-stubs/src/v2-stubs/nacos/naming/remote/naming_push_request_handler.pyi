from _typeshed import Incomplete
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache as ServiceInfoCache
from v2.nacos.naming.model.naming_request import NotifySubscriberRequest as NotifySubscriberRequest
from v2.nacos.naming.model.naming_response import NotifySubscriberResponse as NotifySubscriberResponse
from v2.nacos.transport.model.rpc_request import Request as Request
from v2.nacos.transport.model.rpc_response import Response as Response
from v2.nacos.transport.server_request_handler import IServerRequestHandler as IServerRequestHandler

class NamingPushRequestHandler(IServerRequestHandler):
    def name(self) -> str: ...
    logger: Incomplete
    service_info_cache: Incomplete
    def __init__(self, logger, service_info_cache: ServiceInfoCache) -> None: ...
    async def request_reply(self, request: Request) -> Response | None: ...
