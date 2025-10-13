from v2.nacos.common.constants import Constants as Constants
from v2.nacos.config.encryption.kms_client import KmsClient as KmsClient
from v2.nacos.config.encryption.plugin.kms_encrytion_plugin import KmsEncryptionPlugin as KmsEncryptionPlugin
from v2.nacos.config.model.config_param import HandlerParam as HandlerParam

class KmsAes128EncryptionPlugin(KmsEncryptionPlugin):
    ALGORITHM: str
    def __init__(self, kms_client: KmsClient) -> None: ...
    def generate_secret_key(self, handler_param: HandlerParam) -> HandlerParam: ...
    def algorithm_name(self): ...
