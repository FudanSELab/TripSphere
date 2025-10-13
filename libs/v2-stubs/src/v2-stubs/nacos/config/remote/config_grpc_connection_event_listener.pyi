import asyncio
from _typeshed import Incomplete
from v2.nacos.config.cache.config_subscribe_manager import ConfigSubscribeManager as ConfigSubscribeManager
from v2.nacos.transport.connection_event_listener import ConnectionEventListener as ConnectionEventListener
from v2.nacos.transport.rpc_client import RpcClient as RpcClient

class ConfigGrpcConnectionEventListener(ConnectionEventListener):
    logger: Incomplete
    config_subscribe_manager: Incomplete
    execute_config_listen_channel: Incomplete
    rpc_client: Incomplete
    def __init__(self, logger, config_subscribe_manager: ConfigSubscribeManager, execute_config_listen_channel: asyncio.Queue, rpc_client: RpcClient) -> None: ...
    async def on_connected(self) -> None: ...
    async def on_disconnect(self) -> None: ...
