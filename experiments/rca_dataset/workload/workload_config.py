"""Normal-system workload configuration for the TripSphere dataset."""

import json
import os
from dataclasses import dataclass
from pathlib import Path


def env_value(name: str, legacy_name: str, default: str) -> str:
    return os.getenv(name) or os.getenv(legacy_name) or default


@dataclass(frozen=True)
class RateConfig:
    users: int
    requests_per_second: float


def configured_rate(name: str, users: int, requests_per_second: float) -> RateConfig:
    prefix = f"WORKLOAD_{name.upper()}"
    return RateConfig(
        users=int(os.getenv(f"{prefix}_USERS", str(users))),
        requests_per_second=float(
            os.getenv(f"{prefix}_RPS", str(requests_per_second))
        ),
    )


WORKLOAD_PROFILE = "tripsphere_mixed_realistic_50rps"
AGENT_WORKLOADS = frozenset({"planner", "chat"})

# Application services deployed with TripSphere. Log collection uses this list
# so RCA cases retain the complete application context, while fault topology
# remains defined separately by each case.
BUSINESS_SERVICES = (
    "trip-attraction-service",
    "trip-chat-service",
    "trip-file-service",
    "trip-hotel-service",
    "trip-inventory-service",
    "trip-itinerary-planner",
    "trip-itinerary-service",
    "trip-note-service",
    "trip-order-assistant",
    "trip-order-service",
    "trip-poi-service",
    "trip-product-service",
    "trip-review-service",
    "trip-review-summary",
    "trip-review-summary-worker",
    "trip-user-service",
)

# These are entry-point rates, not internal span or downstream RPC rates.
# Traditional service entry points add up to 50 RPS. Long-running Agent
# requests stay low-rate and are capacity-capped by their fixed user counts.
RATES = {
    "planner": configured_rate("planner", users=20, requests_per_second=0.1),
    "chat": configured_rate("chat", users=10, requests_per_second=0.05),
    "order": configured_rate("order", users=20, requests_per_second=5.0),
    "attraction": configured_rate("attraction", users=40, requests_per_second=12.0),
    "hotel": configured_rate("hotel", users=35, requests_per_second=10.0),
    "product": configured_rate("product", users=25, requests_per_second=8.0),
    "itinerary": configured_rate("itinerary", users=30, requests_per_second=8.0),
    "review_summary": configured_rate(
        "review_summary", users=15, requests_per_second=5.0
    ),
}

TOTAL_USERS = sum(rate.users for rate in RATES.values())
CONFIGURED_RPS = sum(rate.requests_per_second for rate in RATES.values())
TRADITIONAL_RPS = sum(
    rate.requests_per_second
    for name, rate in RATES.items()
    if name not in AGENT_WORKLOADS
)
AGENT_RPS = sum(
    rate.requests_per_second
    for name, rate in RATES.items()
    if name in AGENT_WORKLOADS
)

TRAFFIC_USER_IDS = tuple(
    f"traffic-user-{index:06d}" for index in range(1, 501)
)

ORDER_FLOW_WEIGHTS = {
    "create_then_cancel": 60,
    "create_then_pay": 25,
    "create_pending": 15,
}

ATTRACTION_REQUEST_WEIGHTS = {
    "list_by_city": 40,
    "get_by_id": 40,
    "nearby": 20,
}

HOTEL_REQUEST_WEIGHTS = {
    "list": 35,
    "get_by_id": 25,
    "rooms": 30,
    "nearby": 10,
}

PLANNER_SCENARIOS = (
    {
        "destination": "上海",
        "interests": ["culture", "classic"],
        "pace": "moderate",
        "preferences": "安排经典景点、城市漫步和本地美食。",
        "days": 3,
    },
    {
        "destination": "上海",
        "interests": ["nature", "culture"],
        "pace": "relaxed",
        "preferences": "带老人出行，希望少走路，安排交通方便的景点和舒适午休。",
        "days": 2,
    },
    {
        "destination": "上海",
        "interests": ["classic", "culture"],
        "pace": "moderate",
        "preferences": "以城市文化和经典景点为主，预算适中。",
        "days": 4,
    },
    {
        "destination": "上海",
        "interests": ["culture", "history"],
        "pace": "relaxed",
        "preferences": "带孩子出行，希望安排博物馆、公园和适合儿童的活动。",
        "days": 3,
    },
    {
        "destination": "上海",
        "interests": ["cityscape", "classic"],
        "pace": "intense",
        "preferences": "周末短途旅行，优先安排城市漫步和地标打卡。",
        "days": 2,
    },
)

CHAT_PROMPTS = (
    "请推荐一个上海周末短途旅行方案。",
    "我带老人去杭州两天，哪些景点交通方便、步行少？",
    "请介绍成都适合第一次旅行的美食和文化路线。",
    "北京三日亲子游有哪些适合孩子的景点？",
    "广州周末有哪些适合城市漫步和吃本地美食的安排？",
)

REVIEW_SUMMARY_QUERIES = (
    "这家景点适合带孩子去吗？请总结优缺点。",
    "游客对服务、交通和环境的评价分别是什么？",
    "请根据评论推荐最值得体验的特色。",
    "如果预算有限，游客最常见的建议是什么？",
)

TEST_CITIES = ("上海市",)
FALLBACK_ATTRACTION_IDS = (
    "019cc3b4-3163-751c-9d82-edb85c27c4ae",
    "019cc3b4-3164-70a2-a687-4d53da7fecca",
    "019cc3b4-3164-70a2-a687-4d549890c58b",
)
FALLBACK_HOTEL_IDS = (
    "019cc379-11a6-75a2-9311-802eaab55887",
    "019cc379-11a6-75a2-9311-802f107c54a6",
    "019cc379-11a6-75a2-9311-80303efe0087",
)
FALLBACK_PRODUCT_RESOURCE_IDS = (
    "019cd185-b503-74b2-b8fc-af02fb33ce8c",
    "019cd185-b503-74b2-b8fc-af03afe19383",
)

ORDER_SKU_ENV = "TRIPSPHERE_RCA_ORDER_SKU_ID"
ORDER_DATE_ENV = "TRIPSPHERE_RCA_ORDER_DATE"
DEFAULT_ORDER_SKU_ID = "019cfad0-7d74-700f-8656-04027f6009ae"
ORDER_CATALOG_ENV = "TRIPSPHERE_RCA_ORDER_CATALOG"
ORDER_MIN_DAYS_AHEAD_ENV = "TRIPSPHERE_RCA_ORDER_MIN_DAYS_AHEAD"
ORDER_MAX_DAYS_AHEAD_ENV = "TRIPSPHERE_RCA_ORDER_MAX_DAYS_AHEAD"
PLANNER_SSE_ENV = "TRIPSPHERE_RCA_PLANNER_SSE"


def _seeded_data_path(filename: str) -> Path:
    configured_root = os.getenv("TRIPSPHERE_RCA_SEEDED_DATA_DIR")
    if configured_root:
        return Path(configured_root) / filename
    return (
        Path(__file__).resolve().parents[3]
        / "infra"
        / "initializer"
        / "data"
        / "seeded"
        / "shanghai"
        / filename
    )


def _load_seeded_data(filename: str) -> list[dict]:
    try:
        value = json.loads(
            _seeded_data_path(filename).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _load_attraction_ids() -> tuple[str, ...]:
    ids = tuple(
        item["_id"]
        for item in _load_seeded_data("attractions.json")
        if item.get("_id") and not item.get("temporarilyClosed", False)
    )
    return ids or FALLBACK_ATTRACTION_IDS


def _load_hotel_ids() -> tuple[str, ...]:
    ids = tuple(
        item["_id"]
        for item in _load_seeded_data("hotels.json")
        if item.get("_id")
    )
    return ids or FALLBACK_HOTEL_IDS


def _load_product_resource_ids() -> tuple[str, ...]:
    ids = tuple(
        item["resourceId"]
        for item in _load_seeded_data("spus.json")
        if item.get("resourceType") == "HOTEL_ROOM"
        and item.get("status") == "ON_SHELF"
        and item.get("resourceId")
    )
    return tuple(dict.fromkeys(ids)) or FALLBACK_PRODUCT_RESOURCE_IDS


ATTRACTION_IDS = _load_attraction_ids()
HOTEL_IDS = _load_hotel_ids()
PRODUCT_RESOURCE_IDS = _load_product_resource_ids()


def _order_catalog_path() -> Path:
    configured = os.getenv(ORDER_CATALOG_ENV)
    if configured:
        return Path(configured)
    return _seeded_data_path("spus.json")


def _load_order_sku_ids() -> tuple[str, ...]:
    path = _order_catalog_path()
    try:
        spus = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (DEFAULT_ORDER_SKU_ID,)

    sku_ids = [
        sku["id"]
        for spu in spus
        if spu.get("resourceType") == "HOTEL_ROOM"
        and spu.get("status") == "ON_SHELF"
        for sku in spu.get("skus", [])
        if sku.get("id") and sku.get("status") == "ACTIVE"
    ]
    return tuple(dict.fromkeys(sku_ids)) or (DEFAULT_ORDER_SKU_ID,)


ORDER_SKU_IDS = _load_order_sku_ids()
