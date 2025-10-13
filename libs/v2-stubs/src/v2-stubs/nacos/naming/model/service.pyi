from pydantic import BaseModel
from v2.nacos.common.constants import Constants as Constants
from v2.nacos.common.nacos_exception import NacosException as NacosException
from v2.nacos.naming.model.instance import Instance as Instance

EMPTY: str
ALL_IPS: str
SPLITER: str
DEFAULT_CHARSET: str

class Service(BaseModel):
    name: str
    groupName: str
    clusters: str | None
    cacheMillis: int
    hosts: list[Instance]
    lastRefTime: int
    checksum: str
    allIps: bool
    reachProtectionThreshold: bool
    jsonFromServer: str
    def init_from_key(self, key=None) -> None: ...
    def get_ip_count(self): ...
    def is_expired(self): ...
    def add_host(self, host) -> None: ...
    def add_all_hosts(self, hosts) -> None: ...
    def is_valid(self): ...
    def validate(self): ...
    def get_key_default(self): ...
    def get_key_encoded(self): ...
    def get_grouped_service_name(self): ...
    @staticmethod
    def from_key(key: str): ...
    def get_hosts_str(self): ...
    class Config:
        arbitrary_types_allowed: bool

class ServiceList(BaseModel):
    count: int
    services: list[str]
