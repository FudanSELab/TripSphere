import asyncio
import logging
from typing import Any

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

from review_summary.utils.uuid import uuid7

logger = logging.getLogger(__name__)


async def main() -> None:
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

    base_url = "http://127.0.0.1:24212"
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)

        final_agent_card: AgentCard | None = None
        try:
            logger.info("Attempting to fetch public agent card")
            _public_card = await resolver.get_agent_card()
            logger.info("Successfully fetched public agent card:")
            logger.info(_public_card.model_dump_json(indent=2, exclude_none=True))
            final_agent_card = _public_card
            logger.info(
                "\nUsing PUBLIC agent card for client initialization (default)."
            )

        except Exception as e:
            logger.error(
                f"Critical error fetching public agent card: {e}", exc_info=True
            )
            raise RuntimeError(
                "Failed to fetch the public agent card. Cannot continue."
            ) from e
        client = A2AClient(httpx_client=httpx_client, agent_card=final_agent_card)
        logger.info("A2AClient initialized.")

        test_query = "Just summarize reviews"
        logger.info(f"Sending query: '{test_query}'")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [
                    {"kind": "text", "text": test_query},
                ],
                "message_id": str(uuid7()),
            },
            "metadata": {"target_id": "attraction-001"},
        }

        request = SendMessageRequest(
            id=str(uuid7()),
            params=MessageSendParams.model_validate(send_message_payload),
        )
        response = await client.send_message(request)
        logger.info("Response:")
        logger.info(response.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
