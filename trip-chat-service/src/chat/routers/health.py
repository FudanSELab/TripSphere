import logging
import time
from typing import Any

from fastapi import APIRouter, Response, status

logger = logging.getLogger(__name__)


health = APIRouter(prefix="/health", tags=["Health"])

# Track service start time
_start_time = time.time()


@health.get("")
async def health_check(response: Response) -> dict[str, Any]:
    is_healthy = True  # TODO: Implement health check logic
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "uptime_seconds": round(time.time() - _start_time, 2),
    }
