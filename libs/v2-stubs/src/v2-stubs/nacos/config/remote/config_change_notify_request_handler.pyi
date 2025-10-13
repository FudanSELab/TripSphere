from _typeshed import Incomplete
from v2.nacos.config.cache.config_subscribe_manager import ConfigSubscribeManager as ConfigSubscribeManager
from v2.nacos.config.model.config_request import ConfigChangeNotifyRequest as ConfigChangeNotifyRequest
from v2.nacos.transport.model.internal_response import NotifySubscriberResponse as NotifySubscriberResponse
from v2.nacos.transport.model.rpc_request import Request as Request
from v2.nacos.transport.model.rpc_response import Response as Response
from v2.nacos.transport.server_request_handler import IServerRequestHandler as IServerRequestHandler

class ConfigChangeNotifyRequestHandler(IServerRequestHandler):
    def name(self): ...
    logger: Incomplete
    config_subscribe_manager: Incomplete
    client_name: Incomplete
    def __init__(self, logger, config_subscribe_manager: ConfigSubscribeManager, client_name: str) -> None: ...
    async def request_reply(self, request: Request) -> Response | None: ...
