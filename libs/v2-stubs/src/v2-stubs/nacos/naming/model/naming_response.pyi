from v2.nacos.naming.model.service import Service as Service
from v2.nacos.transport.model.rpc_response import Response as Response

class NotifySubscriberResponse(Response):
    def get_response_type(self) -> str: ...

class SubscribeServiceResponse(Response):
    serviceInfo: Service | None
    def get_response_type(self) -> str: ...
    def get_service_info(self) -> Service: ...

class InstanceResponse(Response):
    def get_response_type(self) -> str: ...

class BatchInstanceResponse(Response):
    def get_response_type(self) -> str: ...

class ServiceListResponse(Response):
    count: int
    serviceNames: list[str]
    def get_response_type(self) -> str: ...
