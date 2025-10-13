from abc import ABC
from v2.nacos.config.model.config import ConfigListenContext as ConfigListenContext
from v2.nacos.transport.model.rpc_request import Request as Request

CONFIG_CHANGE_NOTIFY_REQUEST_TYPE: str

class AbstractConfigRequest(Request, ABC):
    group: str | None
    dataId: str | None
    tenant: str | None
    def get_module(self): ...
    def get_request_type(self) -> str: ...

class ConfigBatchListenRequest(AbstractConfigRequest):
    listen: bool
    configListenContexts: list[ConfigListenContext]
    def get_request_type(self): ...

class ConfigChangeNotifyRequest(AbstractConfigRequest):
    def get_request_type(self): ...

class ConfigQueryRequest(AbstractConfigRequest):
    tag: str | None
    def get_request_type(self): ...

class ConfigPublishRequest(AbstractConfigRequest):
    content: str | None
    casMd5: str | None
    additionMap: dict[str, str]
    def get_request_type(self): ...

class ConfigRemoveRequest(AbstractConfigRequest):
    def get_request_type(self): ...
