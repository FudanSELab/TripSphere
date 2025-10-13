from _typeshed import Incomplete
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import INVALID_PARAM as INVALID_PARAM, INVALID_SERVER_STATUS as INVALID_SERVER_STATUS, NacosException as NacosException
from v2.nacos.transport.auth_client import AuthClient as AuthClient
from v2.nacos.transport.http_agent import HttpAgent as HttpAgent

class NacosServerConnector:
    logger: Incomplete
    client_config: Incomplete
    server_list: Incomplete
    current_index: int
    http_agent: Incomplete
    endpoint: Incomplete
    server_list_lock: Incomplete
    refresh_server_list_internal: int
    auth_client: Incomplete
    def __init__(self, logger, client_config: ClientConfig, http_agent: HttpAgent) -> None: ...
    async def init(self) -> None: ...
    def get_server_list(self): ...
    def get_next_server(self): ...
    async def inject_security_info(self, headers) -> None: ...
