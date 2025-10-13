from _typeshed import Incomplete
from v2.nacos.common.client_config import KMSConfig as KMSConfig
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import INVALID_PARAM as INVALID_PARAM, NacosException as NacosException
from v2.nacos.config.encryption.kms_client import KmsClient as KmsClient
from v2.nacos.config.encryption.plugin.encryption_plugin import EncryptionPlugin as EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_aes_128_encrytion_plugin import KmsAes128EncryptionPlugin as KmsAes128EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_aes_256_encrytion_plugin import KmsAes256EncryptionPlugin as KmsAes256EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_base_encryption_plugin import KmsBaseEncryptionPlugin as KmsBaseEncryptionPlugin
from v2.nacos.config.model.config_param import HandlerParam as HandlerParam

class KMSHandler:
    kms_plugins: dict[str, EncryptionPlugin]
    kms_client: Incomplete
    def __init__(self, kms_config: KMSConfig) -> None: ...
    def find_encryption_service(self, data_id: str): ...
    @staticmethod
    def check_param(handler_param: HandlerParam): ...
    def encrypt_handler(self, handler_param: HandlerParam): ...
    def decrypt_handler(self, handler_param: HandlerParam): ...
