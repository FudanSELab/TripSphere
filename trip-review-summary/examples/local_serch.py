import asyncio

import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient

from review_summary.config.settings import get_settings
from review_summary.models import Entity, TextUnit
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.query.structured_search.local_search.search import LocalSearch
from review_summary.tokenizer.tiktoken import (
    TiktokenTokenizer,
    encoding_name_for_chat_model,
)
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore


async def load_entities() -> list[Entity]:
    df = pd.read_parquet("./tests/fixtures/entities.parquet", dtype_backend="pyarrow")
    entities: list[Entity] = [
        Entity.model_validate(row.to_dict()) for _, row in df.iterrows()
    ]
    return entities


async def load_textunits() -> list[TextUnit]:
    df = pd.read_parquet("./tests/fixtures/text_units.parquet", dtype_backend="pyarrow")
    textunits: list[TextUnit] = [
        TextUnit.model_validate(row.to_dict()) for _, row in df.iterrows()
    ]
    return textunits


async def main() -> None:
    settings = get_settings()

    openai_settings = settings.openai
    chat_model = ChatOpenAI(
        model=openai_settings.chat_model,
        temperature=0.0,
        api_key=openai_settings.api_key,
        base_url=openai_settings.base_url,
    )
    embedding_model = OpenAIEmbeddings(
        model=openai_settings.embedding_model,
        dimensions=openai_settings.embedding_dimensions,
        check_embedding_ctx_length=False,
        api_key=openai_settings.api_key,
        base_url=openai_settings.base_url,
    )
    tokenizer = TiktokenTokenizer(
        encoding_name_for_chat_model(chat_model.model_name)
    )

    neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
    )

    qdrant_client = AsyncQdrantClient(":memory:")
    entity_vector_store = await EntityVectorStore.create_vector_store(qdrant_client)
    text_unit_vector_store = await TextUnitVectorStore.create_vector_store(
        client=qdrant_client
    )
    entities = await load_entities()
    textunits = await load_textunits()
    await entity_vector_store.save_multiple(entities)
    await text_unit_vector_store.save_multiple(text_units=textunits)

    context_builder = LocalSearchMixedContext(
        entity_vector_store=entity_vector_store,
        text_unit_vector_store=text_unit_vector_store,
        embedding_model=embedding_model,
        tokenizer=tokenizer,
        neo4j_driver=neo4j_driver,
    )

    local_search = LocalSearch(
        chat_model=chat_model,
        context_builder=context_builder,
        tokenizer=tokenizer,
        response_type="multiple paragraphs",
    )

    query = "Just summarize the reviews"
    result = await local_search.search(query=query, target_id="attraction-001")

    print("🔍 Query:", query)
    print("\n🤖 Response:\n", result.response)
    if isinstance(result.context_data, dict):
        print("\n📊 Context Records Keys:", list[str](result.context_data.keys()))
    elif isinstance(result.context_data, list):
        print(
            "\n📊 Context Records Keys:",
            [df.columns.tolist() for df in result.context_data],
        )
    else:
        print("\n📊 Context Records Keys:", result.context_data)
    print("\n⏱️  Completion Time:", f"{result.completion_time:.2f}s")
    print(
        "\n🔢 Total Tokens Used (Prompt + Output):",
        result.prompt_tokens + result.output_tokens,
    )

    await neo4j_driver.close()
    await qdrant_client.close()


if __name__ == "__main__":
    asyncio.run(main())
