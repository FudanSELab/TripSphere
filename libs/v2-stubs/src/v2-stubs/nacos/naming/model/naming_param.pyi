from pydantic import BaseModel, Field
from typing import Callable
from v2.nacos.common.constants import Constants as Constants

class RegisterInstanceParam(BaseModel):
    ip: str
    port: int
    weight: float = Field(default=1.0)
    enabled: bool = Field(default=True)
    healthy: bool = Field(default=True)
    metadata: dict[str, str] = Field(default_factory=dict)
    cluster_name: str = Field(default='')
    service_name: str
    group_name: str = Field(default=Constants.DEFAULT_GROUP)
    ephemeral: bool = Field(default=True)

class BatchRegisterInstanceParam(BaseModel):
    service_name: str
    group_name: str
    instances: list[RegisterInstanceParam]

class DeregisterInstanceParam(BaseModel):
    ip: str
    port: int
    cluster_name: str = Field(default='')
    service_name: str
    group_name: str = Field(default=Constants.DEFAULT_GROUP)
    ephemeral: bool = Field(default=True)

class ListInstanceParam(BaseModel):
    service_name: str
    group_name: str
    clusters: list[str]
    subscribe: bool
    healthy_only: bool | None

class SubscribeServiceParam(BaseModel):
    service_name: str
    group_name: str
    clusters: list[str]
    subscribe_callback: Callable | None

class GetServiceParam(BaseModel):
    service_name: str
    group_name: str
    clusters: list[str]

class ListServiceParam(BaseModel):
    namespace_id: str
    group_name: str
    page_no: int
    page_size: int
