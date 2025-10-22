from pydantic import BaseModel, Field


class ServiceDefaults(BaseModel):
    name: str = "trip-chat-service"
    namespace: str = "tripsphere"


class GrpcDefaults(BaseModel):
    port: int = 50057


class NacosDefaults(BaseModel):
    server_address: str = "localhost:8848"
    namespace_id: str = "public"
    group_name: str = "DEFAULT_GROUP"


class MemoryosDefaults(BaseModel):
    short_term_capacity: int = 16
    mid_term_capacity: int = 1024


class MemoryDefaults(BaseModel):
    memoryos: MemoryosDefaults = Field(default_factory=MemoryosDefaults)


class MongodbDefaults(BaseModel):
    uri: str = "mongodb://localhost:27017"
    database: str = "tripsphere_chat_database"


class Defaults(BaseModel):
    service: ServiceDefaults = Field(default_factory=ServiceDefaults)
    grpc: GrpcDefaults = Field(default_factory=GrpcDefaults)
    nacos: NacosDefaults = Field(default_factory=NacosDefaults)
    memory: MemoryDefaults = Field(default_factory=MemoryDefaults)
    mongodb: MongodbDefaults = Field(default_factory=MongodbDefaults)


defaults = Defaults()
