import logging
from typing import Any

from review_summary.index.operations.chunk_text.chunk_text import chunk_text
from review_summary.index.operations.embed_text import embed_text
from review_summary.models import TextUnit
from review_summary.rocketmq.typing import CreateReview
from review_summary.utils.hashing import gen_sha512_hash
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


async def handle_create_review(
    text_unit_vector_store: TextUnitVectorStore, message_body: dict[str, Any]
) -> None:
    """Handle the CreateReview event."""
    create_review = CreateReview.model_validate(message_body, by_alias=True)

    text_chunks = chunk_text([create_review.text])
    text_units: list[TextUnit] = []

    # Generate text embeddings
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
            logger.warning(f"Skipping text unit {idx} due to empty embedding")
            continue
        text_unit_id = gen_sha512_hash({"chunk": text_chunk.text_chunk}, ["chunk"])
        short_id = f"/reviews/{create_review.id}/text-units/{idx}"
        text_unit = TextUnit(
            id=text_unit_id,
            short_id=short_id,
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
    await text_unit_vector_store.save_multiple(text_units)


async def handle_delete_review(message_body: dict[str, Any]) -> None:
    """Handle the DeleteReview event."""


async def handle_update_review(message_body: dict[str, Any]) -> None:
    """Handle the UpdateReview event."""
