"""RocketMQ Consumer standalone entrypoint."""

import asyncio
import logging

from review_summary.config.logging import setup_logging
from review_summary.rocketmq.entrypoint import main

logger = logging.getLogger(__name__)

setup_logging()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
