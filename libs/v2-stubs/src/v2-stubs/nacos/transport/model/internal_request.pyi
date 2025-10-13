import abc
from abc import ABC
from v2.nacos.transport.model.rpc_request import Request as Request

CONNECTION_RESET_REQUEST_TYPE: str
CLIENT_DETECTION_REQUEST_TYPE: str

class InternalRequest(Request, ABC, metaclass=abc.ABCMeta):
    def get_module(self) -> str: ...

class HealthCheckRequest(InternalRequest):
    def get_request_type(self): ...

class ConnectResetRequest(InternalRequest):
    serverIp: str | None
    serverPort: str | None
    def get_request_type(self) -> str: ...

class ClientDetectionRequest(InternalRequest):
    def get_request_type(self) -> str: ...

class ServerCheckRequest(InternalRequest):
    def get_request_type(self): ...

class ConnectionSetupRequest(InternalRequest):
    clientVersion: str | None
    tenant: str | None
    labels: dict
    def get_request_type(self): ...
