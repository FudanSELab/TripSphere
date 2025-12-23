import asyncio

from itinerary.config.logging import setup_logging
from itinerary.server import serve

if __name__ == "__main__":
    setup_logging()
    asyncio.run(serve())
