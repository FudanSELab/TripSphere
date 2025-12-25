from langchain_openai import OpenAIEmbeddings

from review_summary.config.settings import get_settings


async def text_to_embedding(
    text: str, model: str = "text-embedding-3-large"
) -> list[float]:
    """
    Convert text into embedding vectors.

    Args:
        text: Input text to be converted
        model: Embedding model to use

    Returns:
        Embedding vector (list of floats)
    """
    if len(text) == 0:
        raise ValueError("Text must be a non-empty string")
    openai = get_settings().openai
    embedding_model = OpenAIEmbeddings(
        model=model, api_key=openai.api_key, base_url=openai.base_url
    )
    embeddings = await embedding_model.aembed_documents([text])
    return embeddings[0]
