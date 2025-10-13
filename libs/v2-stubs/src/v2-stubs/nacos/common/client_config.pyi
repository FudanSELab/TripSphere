from _typeshed import Incomplete
from v2.nacos.common.auth import StaticCredentialsProvider as StaticCredentialsProvider
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import INVALID_PARAM as INVALID_PARAM, NacosException as NacosException

class KMSConfig:
    enabled: Incomplete
    endpoint: Incomplete
    client_key_content: Incomplete
    password: Incomplete
    access_key: Incomplete
    secret_key: Incomplete
    def __init__(self, enabled: bool = False, endpoint: str = '', access_key: str = '', secret_key: str = '', client_key_content: str = '', password: str = '') -> None: ...

class TLSConfig:
    enabled: Incomplete
    appointed: Incomplete
    ca_file: Incomplete
    cert_file: Incomplete
    key_file: Incomplete
    server_name_override: Incomplete
    def __init__(self, enabled: bool = False, appointed: bool = False, ca_file: str = '', cert_file: str = '', key_file: str = '', server_name_override: str = '') -> None: ...

class GRPCConfig:
    max_receive_message_length: Incomplete
    max_keep_alive_ms: Incomplete
    initial_window_size: Incomplete
    initial_conn_window_size: Incomplete
    grpc_timeout: Incomplete
    def __init__(self, max_receive_message_length=..., max_keep_alive_ms=..., initial_window_size=..., initial_conn_window_size=..., grpc_timeout=...) -> None: ...

class ClientConfig:
    server_list: Incomplete
    endpoint: Incomplete
    endpoint_context_path: Incomplete
    endpoint_query_header: Incomplete
    namespace_id: Incomplete
    credentials_provider: Incomplete
    context_path: Incomplete
    username: Incomplete
    password: Incomplete
    app_name: Incomplete
    app_key: Incomplete
    cache_dir: str
    disable_use_config_cache: bool
    log_dir: Incomplete
    log_level: Incomplete
    log_rotation_backup_count: Incomplete
    timeout_ms: Incomplete
    heart_beat_interval: Incomplete
    kms_config: Incomplete
    tls_config: Incomplete
    grpc_config: Incomplete
    load_cache_at_start: bool
    update_cache_when_empty: bool
    app_conn_labels: Incomplete
    def __init__(self, server_addresses=None, endpoint=None, namespace_id: str = '', context_path: str = '', access_key=None, secret_key=None, username=None, password=None, app_name: str = '', app_key: str = '', log_dir: str = '', log_level=None, log_rotation_backup_count=None, app_conn_labels=None, credentials_provider=None) -> None: ...
    def set_log_level(self, log_level): ...
    def set_cache_dir(self, cache_dir): ...
    def set_log_dir(self, log_dir): ...
    def set_timeout_ms(self, timeout_ms): ...
    def set_heart_beat_interval(self, heart_beat_interval): ...
    def set_tls_config(self, tls_config: TLSConfig): ...
    def set_kms_config(self, kms_config: KMSConfig): ...
    def set_grpc_config(self, grpc_config: GRPCConfig): ...
    def set_load_cache_at_start(self, load_cache_at_start): ...
    def set_update_cache_when_empty(self, update_cache_when_empty: bool): ...
    def set_endpoint_context_path(self, endpoint_context_path): ...
    def set_app_conn_labels(self, app_conn_labels: dict): ...
