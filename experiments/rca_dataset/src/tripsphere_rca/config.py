from __future__ import annotations

import os
from datetime import timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = ROOT / "experiments" / "rca_dataset"
WORKLOAD_ROOT = PACKAGE_ROOT / "workload"
WORKLOAD_PROTO_ROOT = WORKLOAD_ROOT / "proto"
DATASET_ROOT = ROOT / "dataset"
SHANGHAI = timezone(timedelta(hours=8))

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


def env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def iso(value) -> str:
    return value.astimezone(SHANGHAI).isoformat(timespec="seconds")
