from _typeshed import Incomplete
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.nacos_exception import NacosException as NacosException, SERVER_ERROR as SERVER_ERROR
from v2.nacos.transport.http_agent import HttpAgent as HttpAgent

class AuthClient:
    logger: Incomplete
    username: Incomplete
    password: Incomplete
    client_config: Incomplete
    get_server_list: Incomplete
    http_agent: Incomplete
    access_token: Incomplete
    token_ttl: int
    last_refresh_time: int
    token_expired_time: Incomplete
    def __init__(self, logger, client_config: ClientConfig, get_server_list_func, http_agent: HttpAgent) -> None: ...
    async def get_access_token(self, force_refresh: bool = False): ...
