from _typeshed import Incomplete

GRPC_GENERATED_VERSION: str
GRPC_VERSION: Incomplete

class RequestStreamStub:
    requestStream: Incomplete
    def __init__(self, channel) -> None: ...

class RequestStreamServicer:
    def requestStream(self, request, context) -> None: ...

def add_RequestStreamServicer_to_server(servicer, server) -> None: ...

class RequestStream:
    @staticmethod
    def requestStream(request, target, options=(), channel_credentials=None, call_credentials=None, insecure: bool = False, compression=None, wait_for_ready=None, timeout=None, metadata=None): ...

class RequestStub:
    request: Incomplete
    def __init__(self, channel) -> None: ...

class RequestServicer:
    def request(self, request, context) -> None: ...

def add_RequestServicer_to_server(servicer, server) -> None: ...

class Request:
    @staticmethod
    def request(request, target, options=(), channel_credentials=None, call_credentials=None, insecure: bool = False, compression=None, wait_for_ready=None, timeout=None, metadata=None): ...

class BiRequestStreamStub:
    requestBiStream: Incomplete
    def __init__(self, channel) -> None: ...

class BiRequestStreamServicer:
    def requestBiStream(self, request_iterator, context) -> None: ...

def add_BiRequestStreamServicer_to_server(servicer, server) -> None: ...

class BiRequestStream:
    @staticmethod
    def requestBiStream(request_iterator, target, options=(), channel_credentials=None, call_credentials=None, insecure: bool = False, compression=None, wait_for_ready=None, timeout=None, metadata=None): ...
