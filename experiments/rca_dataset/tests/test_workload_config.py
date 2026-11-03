import sys
from pathlib import Path


WORKLOAD_ROOT = Path(__file__).parents[1] / "workload"
if str(WORKLOAD_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKLOAD_ROOT))

from workload_config import (  # noqa: E402
    AGENT_RPS,
    ATTRACTION_IDS,
    BUSINESS_SERVICES,
    CONFIGURED_RPS,
    HOTEL_IDS,
    ORDER_SKU_IDS,
    PRODUCT_RESOURCE_IDS,
    RATES,
    TOTAL_USERS,
    TRADITIONAL_RPS,
)


def test_seeded_catalog_contains_broad_business_id_pools():
    assert len(ATTRACTION_IDS) > 3
    assert len(HOTEL_IDS) > 3
    assert len(PRODUCT_RESOURCE_IDS) > 3
    assert len(ORDER_SKU_IDS) > 1
    assert len(ATTRACTION_IDS) == len(set(ATTRACTION_IDS))
    assert len(HOTEL_IDS) == len(set(HOTEL_IDS))
    assert len(PRODUCT_RESOURCE_IDS) == len(set(PRODUCT_RESOURCE_IDS))
    assert len(ORDER_SKU_IDS) == len(set(ORDER_SKU_IDS))


def test_workload_profile_has_expected_capacity_and_pacing():
    assert TOTAL_USERS == 308
    assert TRADITIONAL_RPS == 198.5
    assert AGENT_RPS == 0.65
    assert CONFIGURED_RPS == 199.15
    assert RATES["planner"].pacing_seconds == 600.0
    assert RATES["order_assistant"].pacing_seconds == 400.0
    assert RATES["review_summary"].pacing_seconds == 20.0
    assert RATES["user_profile"].pacing_seconds == 20.0


def test_business_services_exclude_removed_services():
    assert not {
        "trip-file-service",
        "trip-note-service",
        "trip-poi-service",
    } & set(BUSINESS_SERVICES)
