import abc
from abc import ABC, abstractmethod
from v2.nacos.transport.model.internal_request import ClientDetectionRequest as ClientDetectionRequest
from v2.nacos.transport.model.internal_response import ClientDetectionResponse as ClientDetectionResponse
from v2.nacos.transport.model.rpc_request import Request as Request
from v2.nacos.transport.model.rpc_response import Response as Response

class IServerRequestHandler(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    async def request_reply(self, request: Request) -> Response | None: ...

class ClientDetectionRequestHandler(IServerRequestHandler):
    def name(self) -> str: ...
    async def request_reply(self, request: Request) -> Response | None: ...
