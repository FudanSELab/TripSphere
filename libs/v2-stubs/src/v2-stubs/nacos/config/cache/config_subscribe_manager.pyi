import asyncio
from _typeshed import Incomplete
from logging import Logger
from typing import Callable
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.config.cache.config_info_cache import ConfigInfoCache as ConfigInfoCache
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager as ConfigFilterChainManager
from v2.nacos.config.model.config import SubscribeCacheData as SubscribeCacheData
from v2.nacos.config.util.config_client_util import get_config_cache_key as get_config_cache_key
from v2.nacos.utils import md5_util as md5_util
from v2.nacos.utils.md5_util import md5 as md5

class ConfigSubscribeManager:
    subscribe_cache_map: dict[str, SubscribeCacheData]
    logger: Incomplete
    lock: Incomplete
    namespace_id: Incomplete
    config_filter_chain_manager: Incomplete
    config_info_cache: Incomplete
    execute_config_listen_channel: Incomplete
    def __init__(self, logger: Logger, config_info_cache: ConfigInfoCache, namespace_id: str, config_filter_chain_manager: ConfigFilterChainManager, execute_config_listen_channel: asyncio.Queue) -> None: ...
    async def add_listener(self, data_id: str, group_name: str, tenant: str, listener: Callable | None): ...
    async def remove_listener(self, data_id: str, group_name: str, tenant: str, listener: Callable | None): ...
    async def notify_config_changed(self, data_id: str, group_name: str, tenant: str): ...
    async def batch_set_config_changed(self, task_id: int): ...
    async def update_subscribe_cache(self, data_id: str, group_name: str, tenant: str, content: str, encrypted_data_key: str): ...
    async def execute_listener_and_build_tasks(self, is_sync_all: bool): ...
