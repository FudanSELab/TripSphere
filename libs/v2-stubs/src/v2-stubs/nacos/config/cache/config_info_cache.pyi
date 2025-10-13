from _typeshed import Incomplete
from v2.nacos.common.client_config import ClientConfig as ClientConfig
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.config.util.config_client_util import get_config_cache_key as get_config_cache_key
from v2.nacos.utils.file_util import read_file as read_file, write_to_file as write_to_file

FAILOVER_FILE_SUFFIX: str
ENCRYPTED_DATA_KEY_FILE_NAME: str

class ConfigInfoCache:
    logger: Incomplete
    config_cache_dir: Incomplete
    namespace_id: Incomplete
    def __init__(self, client_config: ClientConfig) -> None: ...
    async def write_config_to_cache(self, cache_key: str, content: str, encrypted_data_key: str): ...
    async def get_config_cache(self, data_id: str, group: str): ...
    async def get_fail_over_config_cache(self, data_id: str, group: str): ...
