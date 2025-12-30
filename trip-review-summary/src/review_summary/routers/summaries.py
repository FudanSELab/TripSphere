from fastapi import APIRouter

summaries = APIRouter(prefix="/summaries", tags=["Summaries"])


@summaries.get("")
async def get_static_summary(target_id: str, target_type: str) -> str:
    raise NotImplementedError
