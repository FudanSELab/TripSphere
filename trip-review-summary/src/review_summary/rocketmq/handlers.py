import logging
from typing import Any

from review_summary.index.operations.chunk_text.chunk_text import chunk_text
from review_summary.index.operations.embed_text import embed_text
from review_summary.models import TextUnit
from review_summary.rocketmq.typing import CreateReview
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


async def handle_create_review(
    text_unit_vector_store: TextUnitVectorStore, message_body: dict[str, Any]
) -> None:
    """Handle the CreateReview event."""
    create_review = CreateReview.model_validate(message_body, by_alias=True)

    logger.debug(f"Chunking for review {create_review.id}")
    text_chunks = chunk_text([create_review.text], encoding_name="cl100k_base")
    text_units: list[TextUnit] = []

    # Generate text embeddings
    logger.debug(f"Generating embeddings for review {create_review.id}")
    embeddings = await embed_text(
        texts=[text_chunk.text_chunk for text_chunk in text_chunks],
        model_config={
            "model_name": "text-embedding-3-large",
            "encoding_name": "cl100k_base",
        },
    )

    # Create basic text units with embeddings
    for idx, (text_chunk, embedding) in enumerate(
        zip(text_chunks, embeddings, strict=True)
    ):
        if embedding is None:
            logger.warning(f"Skip text unit {idx} due to empty embedding")
            continue
        readable_id = f"/reviews/{create_review.id}/text-units/{idx}"
        text_unit = TextUnit(
            readable_id=readable_id,
            text=text_chunk.text_chunk,
            embedding=embedding,
            n_tokens=text_chunk.n_tokens,
            document_id=create_review.id,
            attributes={
                "target_id": create_review.target_id,
                "target_type": "attraction",
            },
        )
        text_units.append(text_unit)

    # Save to text unit vector store
    logger.debug(f"Saving {len(text_units)} text units for review {create_review.id}")
    await text_unit_vector_store.save_multiple(text_units)


async def handle_delete_review(message_body: dict[str, Any]) -> None:
    """Handle the DeleteReview event."""


async def handle_update_review(message_body: dict[str, Any]) -> None:
    """Handle the UpdateReview event."""
