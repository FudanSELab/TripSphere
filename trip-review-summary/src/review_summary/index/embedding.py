from langchain_openai import OpenAIEmbeddings

from review_summary.config.settings import get_settings


async def text_to_embedding_async(
    text: str, model: str = "text-embedding-3-large"
) -> list[float]:
    """
    Utility function to convert text into embedding vectors (asynchronous).

    Args:
        text: input text
        model: embedding model to use, default is "text-embedding-ada-002"
        api_key: OpenAI API key; if None the key from environment variables will be used

    Returns:
        Embedding vector (list of floats)
    """
    settings = get_settings()
    API_KEY = settings.openai.api_key
    BASE_URL = settings.openai.base_url
    if len(text) == 0:
        raise ValueError("Text must be a non-empty string")

    # Create embedding instance
    embedding_llm = OpenAIEmbeddings(model=model, api_key=API_KEY, base_url=BASE_URL)

    # Asynchronously generate embedding vectors
    embeddings = await embedding_llm.aembed_documents([text])

    # Return the first (and only) embedding vector
    return embeddings[0]
