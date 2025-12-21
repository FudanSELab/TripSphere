import asyncio
from typing import List

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


def text_to_embedding(text: str, model: str = "text-embedding-3-large") -> List[float]:
    """
    Utility function to convert text into embedding vectors (synchronous).
    Make sure the API key is configured in the .env file before use.
    Args:
        text: input text
        model: embedding model to use, default is "text-embedding-ada-002"

    Returns:
        Embedding vector (list of floats)
    """
    if not text or not isinstance(text, str):
        raise ValueError("Text must be a non-empty string")

    # Create embedding instance
    embedding_llm = OpenAIEmbeddings(model=model)

    # Generate embedding vectors
    embeddings = embedding_llm.embed_documents([text])

    # Return the first (and only) embedding vector
    return embeddings[0]


async def text_to_embedding_async(
    text: str, model: str = "text-embedding-3-large"
) -> List[float]:
    """
    Utility function to convert text into embedding vectors (asynchronous).

    Args:
        text: input text
        model: embedding model to use, default is "text-embedding-ada-002"
        api_key: OpenAI API key; if None the key from environment variables will be used

    Returns:
        Embedding vector (list of floats)
    """
    if not text or not isinstance(text, str):
        raise ValueError("Text must be a non-empty string")

    # Create embedding instance
    embedding_llm = OpenAIEmbeddings(model=model)

    # Asynchronously generate embedding vectors
    embeddings = await embedding_llm.aembed_documents([text])

    # Return the first (and only) embedding vector
    return embeddings[0]


# Example usage
if __name__ == "__main__":
    # Synchronous example
    try:
        load_dotenv()
        text = "This is a test text for embedding."
        embedding = text_to_embedding(text)
        print(f"Length of embedding: {len(embedding)}")
        print(f"Top five value: {embedding[:5]}")
    except Exception as e:
        print(f"Error: {e}")

    # Asynchronous example
    async def async_test():
        try:
            text = "This is a test text for asynchronous embedding."
            embedding = await text_to_embedding_async(text)
            print(f"Length of embedding: {len(embedding)}")
            print(f"Top five value: {embedding[:5]}")
        except Exception as e:
            print(f"Error: {e}")

    # Run async example
    asyncio.run(async_test())
