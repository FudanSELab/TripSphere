from _typeshed import Incomplete
from v2.nacos.common.client_config import TLSConfig as TLSConfig

HTTP_STATUS_SUCCESS: int

class HttpAgent:
    logger: Incomplete
    tls_config: Incomplete
    default_timeout: Incomplete
    ssl_context: Incomplete
    def __init__(self, logger, tls_config: TLSConfig, default_timeout) -> None: ...
    async def request(self, url: str, method: str, headers: dict = None, params: dict = None, data: dict = None): ...
