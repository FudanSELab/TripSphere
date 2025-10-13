from _typeshed import Incomplete
from pydantic import BaseModel
from typing import Callable
from v2.nacos.common.nacos_exception import INVALID_PARAM as INVALID_PARAM, NacosException as NacosException
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager as ConfigFilterChainManager
from v2.nacos.config.model.config_param import ConfigParam as ConfigParam, UsageType as UsageType

class ConfigItem(BaseModel):
    id: str
    dataId: str
    group: str
    content: str
    md5: str | None
    tenant: str
    appname: str

class ConfigPage(BaseModel):
    totalCount: int
    pageNumber: int
    pagesAvailable: int
    pageItems: list[ConfigItem]

class ConfigListenContext(BaseModel):
    group: str
    md5: str
    dataId: str
    tenant: str

class ConfigContext(BaseModel):
    group: str
    dataId: str
    tenant: str

class SubscribeCacheData:
    data_id: Incomplete
    group: Incomplete
    tenant: Incomplete
    content: Incomplete
    content_type: Incomplete
    md5: Incomplete
    cache_data_listeners: list[CacheDataListenerWrap]
    encrypted_data_key: Incomplete
    task_id: int
    config_chain_manager: Incomplete
    is_sync_with_server: Incomplete
    lock: Incomplete
    def __init__(self, data_id: str, group: str, tenant: str, content: str, md5: str, encrypted_data_key: str, chain_manager: ConfigFilterChainManager, content_type: str = '', is_sync_with_server: bool = False) -> None: ...
    async def add_listener(self, listener: Callable | None): ...
    async def remove_listener(self, listener: Callable | None): ...
    async def execute_listener(self) -> None: ...

class CacheDataListenerWrap:
    listener: Incomplete
    last_md5: Incomplete
    def __init__(self, listener: Callable, last_md5) -> None: ...
    def __eq__(self, other): ...
    def __hash__(self): ...
