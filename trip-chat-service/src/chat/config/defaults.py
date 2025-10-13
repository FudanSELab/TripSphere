from pydantic import BaseModel, Field


class ServiceDefaults(BaseModel):
    name: str = "trip-chat-service"
    namespace: str = "tripsphere"


class GrpcDefaults(BaseModel):
    port: int = 50057


class NacosDefaults(BaseModel):
    server_address: str = "nacos:8848"
    namespace_id: str = "public"
    group_name: str = "DEFAULT_GROUP"


class Defaults(BaseModel):
    service: ServiceDefaults = Field(default_factory=ServiceDefaults)
    grpc: GrpcDefaults = Field(default_factory=GrpcDefaults)
    nacos: NacosDefaults = Field(default_factory=NacosDefaults)


defaults = Defaults()
