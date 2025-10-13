from _typeshed import Incomplete

CLIENT_INVALID_PARAM: int
CLIENT_DISCONNECT: int
CLIENT_OVER_THRESHOLD: int
INVALID_PARAM: int
NO_RIGHT: int
NOT_FOUND: int
CONFLICT: int
SERVER_ERROR: int
BAD_GATEWAY: int
OVER_THRESHOLD: int
INVALID_SERVER_STATUS: int
UN_REGISTER: int
NO_HANDLER: int
INVALID_INTERFACE_ERROR: int
RESOURCE_NOT_FOUND: int
HTTP_CLIENT_ERROR_CODE: int

class NacosException(Exception):
    error_code: Incomplete
    message: Incomplete
    def __init__(self, error_code, message: str = 'An error occurred') -> None: ...
