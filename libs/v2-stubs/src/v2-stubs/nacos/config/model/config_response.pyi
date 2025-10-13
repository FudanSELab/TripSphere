from pydantic import BaseModel
from v2.nacos.transport.model.rpc_response import Response as Response

class ConfigContext(BaseModel):
    group: str
    dataId: str
    tenant: str

class ConfigChangeBatchListenResponse(Response):
    changedConfigs: list[ConfigContext]
    def get_response_type(self) -> str: ...

class ConfigQueryResponse(Response):
    content: str | None
    encryptedDataKey: str | None
    contentType: str | None
    md5: str | None
    lastModified: int | None
    isBeta: bool
    tag: bool
    def get_response_type(self) -> str: ...

class ConfigPublishResponse(Response):
    def get_response_type(self) -> str: ...

class ConfigRemoveResponse(Response):
    def get_response_type(self) -> str: ...
