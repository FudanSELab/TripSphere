from _typeshed import Incomplete
from typing import Callable
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import CLIENT_OVER_THRESHOLD as CLIENT_OVER_THRESHOLD, NacosException as NacosException, SERVER_ERROR as SERVER_ERROR
from v2.nacos.config.cache.config_info_cache import ConfigInfoCache as ConfigInfoCache
from v2.nacos.config.cache.config_subscribe_manager import ConfigSubscribeManager as ConfigSubscribeManager
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager as ConfigFilterChainManager
from v2.nacos.config.model.config import ConfigListenContext as ConfigListenContext
from v2.nacos.config.model.config_param import ConfigParam as ConfigParam
from v2.nacos.config.model.config_request import AbstractConfigRequest as AbstractConfigRequest, CONFIG_CHANGE_NOTIFY_REQUEST_TYPE as CONFIG_CHANGE_NOTIFY_REQUEST_TYPE, ConfigBatchListenRequest as ConfigBatchListenRequest, ConfigPublishRequest as ConfigPublishRequest, ConfigQueryRequest as ConfigQueryRequest, ConfigRemoveRequest as ConfigRemoveRequest
from v2.nacos.config.model.config_response import ConfigChangeBatchListenResponse as ConfigChangeBatchListenResponse, ConfigPublishResponse as ConfigPublishResponse, ConfigQueryResponse as ConfigQueryResponse, ConfigRemoveResponse as ConfigRemoveResponse
from v2.nacos.config.remote.config_change_notify_request_handler import ConfigChangeNotifyRequestHandler as ConfigChangeNotifyRequestHandler
from v2.nacos.config.remote.config_grpc_connection_event_listener import ConfigGrpcConnectionEventListener as ConfigGrpcConnectionEventListener
from v2.nacos.config.util.config_client_util import get_config_cache_key as get_config_cache_key
from v2.nacos.transport.http_agent import HttpAgent as HttpAgent
from v2.nacos.transport.nacos_server_connector import NacosServerConnector as NacosServerConnector
from v2.nacos.transport.rpc_client import ConnectionType as ConnectionType, RpcClient as RpcClient
from v2.nacos.transport.rpc_client_factory import RpcClientFactory as RpcClientFactory
from v2.nacos.utils.common_util import get_current_time_millis as get_current_time_millis
from v2.nacos.utils.md5_util import md5 as md5

class ConfigGRPCClientProxy:
    logger: Incomplete
    client_config: Incomplete
    namespace_id: Incomplete
    nacos_server_connector: Incomplete
    config_info_cache: Incomplete
    uuid: Incomplete
    app_name: Incomplete
    rpc_client_manager: Incomplete
    execute_config_listen_channel: Incomplete
    stop_event: Incomplete
    listen_task: Incomplete
    last_all_sync_time: Incomplete
    config_subscribe_manager: Incomplete
    def __init__(self, client_config: ClientConfig, http_agent: HttpAgent, config_info_cache: ConfigInfoCache, config_filter_chain_manager: ConfigFilterChainManager) -> None: ...
    async def start(self) -> None: ...
    async def fetch_rpc_client(self, task_id: int = 0) -> RpcClient: ...
    async def request_config_server(self, rpc_client: RpcClient, request: AbstractConfigRequest, response_class): ...
    async def query_config(self, data_id: str, group: str): ...
    async def publish_config(self, param: ConfigParam): ...
    async def remove_config(self, group: str, data_id: str): ...
    async def add_listener(self, data_id: str, group: str, listener: Callable) -> None: ...
    async def remove_listener(self, data_id: str, group: str, listener: Callable): ...
    async def server_health(self): ...
    async def close_client(self) -> None: ...
