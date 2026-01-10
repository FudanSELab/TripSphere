from pydantic import BaseModel, Field


class FinalizeGraphConfig(BaseModel):
    """Configuration for finalize_graph task."""

    # For embed_graph operation
    embed_graph_enabled: bool = Field(
        default=False,
        description="A flag indicating whether to enable graph embedding.",
    )
    vector_dimension: int = Field(
        default=256,
        description="The graph embedding vector dimension.",
    )
    graph_name: str | None = Field(
        default=None,
        description="The name of in-memory projected graph in Neo4j GDS.",
    )
