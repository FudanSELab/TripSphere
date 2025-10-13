from abc import ABC
from v2.nacos.naming.model.instance import Instance as Instance
from v2.nacos.naming.model.service import Service as Service
from v2.nacos.transport.model.rpc_request import Request as Request

class AbstractNamingRequest(Request, ABC):
    namespace: str | None
    serviceName: str | None
    groupName: str | None
    def get_module(self): ...
    def get_request_type(self) -> str: ...

NOTIFY_SUBSCRIBER_REQUEST_TYPE: str

class InstanceRequest(AbstractNamingRequest):
    type: str | None
    instance: Instance | None
    def get_request_type(self) -> str: ...

class PersistentInstanceRequest(AbstractNamingRequest):
    type: str | None
    instance: Instance | None
    def get_request_type(self) -> str: ...

class BatchInstanceRequest(AbstractNamingRequest):
    type: str | None
    instances: list[Instance] | None
    def get_request_type(self) -> str: ...

class NotifySubscriberRequest(AbstractNamingRequest):
    serviceInfo: Service | None
    def get_request_type(self) -> str: ...

class ServiceListRequest(AbstractNamingRequest):
    pageNo: int | None
    pageSize: int | None
    def get_request_type(self) -> str: ...

class SubscribeServiceRequest(AbstractNamingRequest):
    subscribe: bool | None
    clusters: str | None
    def get_request_type(self) -> str: ...
