import asyncio

import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from tiktoken import encoding_name_for_model

from review_summary.config.settings import get_settings
from review_summary.models import Entity, TextUnit
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.query.structured_search.local_search.search import LocalSearch
from review_summary.tokenizer.tiktoken import TiktokenTokenizer
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

settings = get_settings()


async def load_entities() -> list[Entity]:
    df = pd.read_parquet("./tests/fixtures/entities.parquet", dtype_backend="pyarrow")
    entities = []
    for _, row in df.iterrows():
        entity = Entity.model_validate(row.to_dict())
        entities.append(entity)
    return entities


async def load_textunits() -> list[TextUnit]:
    df = pd.read_parquet("./tests/fixtures/text_units.parquet", dtype_backend="pyarrow")
    textunits = []
    for _, row in df.iterrows():
        textunit = TextUnit.model_validate(row.to_dict())
        textunits.append(textunit)
    return textunits


async def main():
    entities = await load_entities()
    textunits = await load_textunits()
    openai_settings = get_settings().openai
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        api_key=openai_settings.api_key.get_secret_value(),
        base_url=openai_settings.base_url,
    )
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=openai_settings.api_key.get_secret_value(),
        base_url=openai_settings.base_url,
    )

    tokenizer = TiktokenTokenizer(encoding_name_for_model(llm.model_name))

    neo4j_driver = AsyncGraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
    )

    qdrant_client = AsyncQdrantClient(":memory:")
    entity_store = await EntityVectorStore.create_vector_store(qdrant_client)
    await entity_store.save_multiple(entities)
    textunit_store = await TextUnitVectorStore.create_vector_store(qdrant_client)
    await textunit_store.save_multiple(text_units=textunits)

    context_builder = LocalSearchMixedContext(
        entity_text_embeddings=entity_store,
        text_unit_store=textunit_store,
        text_embedder=embedder,
        tokenizer=tokenizer,
        neo4j_driver=neo4j_driver,
    )

    local_search = LocalSearch(
        model=llm,
        context_builder=context_builder,
        tokenizer=tokenizer,
        response_type="multiple paragraphs",
    )

    query = "Just summarize review"

    result = await local_search.search(query=query, target_id="attraction-001")

    print("🔍 Query:", query)
    print("\n🤖 Response:\n", result.response)
    print("\n📊 Context Records Keys:", list(result.context_data.keys()))
    print("\n⏱️  Completion Time:", f"{result.completion_time:.2f}s")
    print(
        "\n🔢 Total Tokens Used (Prompt + Output):",
        result.prompt_tokens + result.output_tokens,
    )

    await neo4j_driver.close()
    await qdrant_client.close()


if __name__ == "__main__":
    asyncio.run(main())
