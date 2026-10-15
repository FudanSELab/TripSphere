from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests


def collect_logs(
    url: str,
    case_id: str,
    services: tuple[str, ...],
    start: datetime,
    end: datetime,
    path,
    chunk_seconds: int = 15,
    limit: int = 1000,
) -> int:
    rows: list[dict[str, Any]] = []
    for service in services:
        current = start
        while current < end:
            chunk_end = min(current + timedelta(seconds=chunk_seconds), end)
            response = requests.get(
                f"{url.rstrip('/')}/loki/api/v1/query_range",
                params={
                    "query": f'{{service_name="{service}"}}',
                    "start": int(current.timestamp() * 1e9),
                    "end": int(chunk_end.timestamp() * 1e9),
                    "limit": limit,
                    "direction": "forward",
                },
                timeout=(5, 120),
            )
            response.raise_for_status()
            for stream in response.json().get("data", {}).get("result", []):
                labels = json.dumps(stream.get("stream", {}), ensure_ascii=False)
                for timestamp_ns, line in stream.get("values", []):
                    rows.append({
                        "case_id": case_id,
                        "service_name": service,
                        "timestamp_ns": int(timestamp_ns),
                        "line": line,
                        "labels_json": labels,
                    })
            if chunk_end >= end:
                break
            current = chunk_end
    frame = pd.DataFrame(rows, columns=[
        "case_id", "service_name", "timestamp_ns", "line", "labels_json",
    ])
    if not frame.empty:
        frame = frame.drop_duplicates(
            subset=["service_name", "timestamp_ns", "line"]
        ).sort_values(["timestamp_ns", "service_name"])
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp_ns"], unit="ns", utc=True
        ).map(lambda value: value.isoformat())
    else:
        frame["timestamp"] = pd.Series(dtype="string")
    frame.to_parquet(path, index=False)
    return len(frame)
