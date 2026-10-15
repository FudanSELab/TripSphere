from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from tripsphere_rca.config import BUSINESS_SERVICES


def workload_summary(path: Path, target: str) -> dict[str, Any]:
    stats = path / "locust_stats.csv"
    if not stats.exists():
        return {}
    with stats.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("Name") != "Aggregated"]
    if not rows:
        return {}
    return {
        "target": target,
        "services": list(BUSINESS_SERVICES),
        "request_count": sum(int(row.get("Request Count") or 0) for row in rows),
        "failure_count": sum(int(row.get("Failure Count") or 0) for row in rows),
        "request_counts_by_operation": {
            row["Name"]: int(row.get("Request Count") or 0) for row in rows
        },
    }
