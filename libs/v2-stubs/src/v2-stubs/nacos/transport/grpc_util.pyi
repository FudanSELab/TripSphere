from _typeshed import Incomplete
from v2.nacos.common.nacos_exception import NacosException as NacosException, SERVER_ERROR as SERVER_ERROR
from v2.nacos.config.model.config_request import ConfigChangeNotifyRequest as ConfigChangeNotifyRequest
from v2.nacos.config.model.config_response import ConfigChangeBatchListenResponse as ConfigChangeBatchListenResponse, ConfigPublishResponse as ConfigPublishResponse, ConfigQueryResponse as ConfigQueryResponse, ConfigRemoveResponse as ConfigRemoveResponse
from v2.nacos.naming.model.naming_request import NotifySubscriberRequest as NotifySubscriberRequest
from v2.nacos.naming.model.naming_response import BatchInstanceResponse as BatchInstanceResponse, InstanceResponse as InstanceResponse, ServiceListResponse as ServiceListResponse, SubscribeServiceResponse as SubscribeServiceResponse
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2 import Metadata as Metadata, Payload as Payload
from v2.nacos.transport.model import ServerCheckResponse as ServerCheckResponse
from v2.nacos.transport.model.internal_request import ClientDetectionRequest as ClientDetectionRequest
from v2.nacos.transport.model.internal_response import ErrorResponse as ErrorResponse, HealthCheckResponse as HealthCheckResponse
from v2.nacos.transport.model.rpc_request import Request as Request
from v2.nacos.transport.model.rpc_response import Response as Response
from v2.nacos.utils.net_util import NetUtils as NetUtils

class GrpcUtils:
    SERVICE_INFO_KEY: str
    remote_type: Incomplete
    @staticmethod
    def convert_request_to_payload(request: Request): ...
    @staticmethod
    def convert_response_to_payload(response: Response): ...
    @staticmethod
    def parse(payload: Payload): ...
    @staticmethod
    def to_json(obj): ...

def parse_payload_to_response(payload): ...
