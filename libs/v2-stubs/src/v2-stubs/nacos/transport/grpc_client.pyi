from _typeshed import Incomplete
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import CLIENT_DISCONNECT as CLIENT_DISCONNECT, NacosException as NacosException
from v2.nacos.transport.connection import Connection as Connection
from v2.nacos.transport.grpc_connection import GrpcConnection as GrpcConnection
from v2.nacos.transport.grpc_util import GrpcUtils as GrpcUtils
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2_grpc import BiRequestStreamStub as BiRequestStreamStub, RequestStub as RequestStub
from v2.nacos.transport.model.internal_request import ConnectionSetupRequest as ConnectionSetupRequest, ServerCheckRequest as ServerCheckRequest
from v2.nacos.transport.model.internal_response import ServerCheckResponse as ServerCheckResponse
from v2.nacos.transport.model.rpc_request import Request as Request
from v2.nacos.transport.model.server_info import ServerInfo as ServerInfo
from v2.nacos.transport.nacos_server_connector import NacosServerConnector as NacosServerConnector
from v2.nacos.transport.rpc_client import ConnectionType as ConnectionType, RpcClient as RpcClient

class GrpcClient(RpcClient):
    logger: Incomplete
    tls_config: Incomplete
    grpc_config: Incomplete
    tenant: Incomplete
    def __init__(self, logger, name: str, client_config: ClientConfig, nacos_server: NacosServerConnector) -> None: ...
    async def connect_to_server(self, server_info: ServerInfo) -> Connection | None: ...
    def get_connection_type(self): ...
    def get_rpc_port_offset(self) -> int: ...
