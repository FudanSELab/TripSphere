from pydantic import BaseModel, Field


class ServiceDefaults(BaseModel):
    name: str = "trip-itinerary-planner"
    namespace: str = "tripsphere"


class GrpcDefaults(BaseModel):
    port: int = 50059


class NacosDefaults(BaseModel):
    enabled: bool = True  # Set to False to disable Nacos registration
    server_address: str = "nacos:8848"
    namespace_id: str = "public"
    group_name: str = "DEFAULT_GROUP"


class LLMDefaults(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4000
    base_url: str | None = None  # Optional custom API base URL


class Defaults(BaseModel):
    service: ServiceDefaults = Field(default_factory=ServiceDefaults)
    grpc: GrpcDefaults = Field(default_factory=GrpcDefaults)
    nacos: NacosDefaults = Field(default_factory=NacosDefaults)
    llm: LLMDefaults = Field(default_factory=LLMDefaults)


defaults = Defaults()

