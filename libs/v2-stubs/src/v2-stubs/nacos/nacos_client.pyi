from _typeshed import Incomplete
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.nacos_exception import INVALID_PARAM as INVALID_PARAM, NacosException as NacosException
from v2.nacos.transport.http_agent import HttpAgent as HttpAgent

class NacosClient:
    logger: Incomplete
    client_config: Incomplete
    http_agent: Incomplete
    def __init__(self, client_config: ClientConfig, log_file: str) -> None: ...
    def init_log(self, client_config: ClientConfig, module): ...
