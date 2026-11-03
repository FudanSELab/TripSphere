from __future__ import annotations

import base64
import json
import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import requests

TRACE_COLUMNS = [
    "case_id",
    "trace_id",
    "span_id",
    "parent_span_id",
    "service_name",
    "span_name",
    "operation_name",
    "method_name",
    "span_kind",
    "start_time_unix_nano",
    "start_time",
    "end_time_unix_nano",
    "duration_ns",
    "duration_ms",
    "status_code",
    "status_json",
    "attributes_json",
    "resource_attributes_json",
    "scope_name",
    "scope_version",
    "trace_root_service_name",
    "trace_root_span_name",
    "source",
]

_thread_local = threading.local()


def collect_traces(
    url: str,
    case_id: str,
    start: datetime,
    end: datetime,
    path,
    query_service: str | None = None,
    chunk_seconds: int = 30,
    limit: int = 1000,
    max_workers: int = 16,
) -> int:
    if chunk_seconds <= 0:
        raise ValueError("trace search chunk_seconds must be positive")
    if limit <= 0:
        raise ValueError("trace search limit must be positive")
    if max_workers <= 0:
        raise ValueError("trace detail max_workers must be positive")

    base_url = url.rstrip("/")
    traces: dict[str, dict[str, Any]] = {}
    current = start
    with requests.Session() as search_session:
        while current < end:
            chunk_end = min(current + timedelta(seconds=chunk_seconds), end)
            start_seconds, end_seconds = _search_bounds(current, chunk_end)
            params = {
                "start": start_seconds,
                "end": end_seconds,
                "limit": limit,
            }
            if query_service:
                params["tags"] = f'service.name="{query_service}"'
            response = search_session.get(
                f"{base_url}/api/search", params=params, timeout=(5, 120)
            )
            response.raise_for_status()
            for trace in response.json().get("traces", []):
                trace_id = trace.get("traceID")
                normalized_trace_id = _normalize_trace_id(trace_id)
                if normalized_trace_id:
                    traces.setdefault(normalized_trace_id, trace)
            if chunk_end >= end:
                break
            current = chunk_end

    trace_items = sorted(
        traces.items(), key=lambda item: int(item[1].get("startTimeUnixNano", 0) or 0)
    )
    rows: list[dict[str, Any]] = []
    batch_size = max_workers * 4
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for offset in range(0, len(trace_items), batch_size):
            detail_rows = executor.map(
                lambda item: _fetch_and_flatten_trace(
                    base_url, item[0], item[1], case_id, start, end
                ),
                trace_items[offset : offset + batch_size],
            )
            rows.extend(row for trace_rows in detail_rows for row in trace_rows)
    frame = pd.DataFrame(rows, columns=TRACE_COLUMNS)
    frame.to_parquet(path, index=False)
    return len(frame)


def _fetch_and_flatten_trace(
    base_url: str,
    trace_id: str,
    search_trace: dict[str, Any],
    case_id: str,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        _thread_local.session = session
    request_trace_id = str(search_trace.get("traceID") or trace_id)
    response = session.get(f"{base_url}/api/traces/{request_trace_id}", timeout=(5, 120))
    response.raise_for_status()
    detail = response.json() or search_trace
    return _flatten_trace(detail, trace_id, search_trace, case_id, start, end)


def _flatten_trace(
    detail: dict[str, Any],
    trace_id: str,
    search_trace: dict[str, Any],
    case_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in detail.get("batches", []):
        resource_attributes = _attributes(
            batch.get("resource", {}).get("attributes", [])
        )
        service_name = str(resource_attributes.get("service.name", "") or "")
        for scope_spans in batch.get("scopeSpans", []):
            scope = scope_spans.get("scope", {})
            for span in scope_spans.get("spans", []):
                attributes = _attributes(span.get("attributes", []))
                start_ns = _integer(span.get("startTimeUnixNano"))
                end_ns = _integer(span.get("endTimeUnixNano"))
                duration_ns = max(end_ns - start_ns, 0) if start_ns and end_ns else 0
                span_name = str(span.get("name", "") or "")
                rows.append({
                    "case_id": case_id,
                    "trace_id": _normalize_trace_id(trace_id),
                    "span_id": _decode_otel_id(span.get("spanId")),
                    "parent_span_id": _decode_otel_id(span.get("parentSpanId")),
                    "service_name": service_name,
                    "span_name": span_name,
                    "operation_name": span_name,
                    "method_name": _first_attribute(
                        attributes, "http.request.method", "rpc.method"
                    ),
                    "span_kind": span.get("kind", ""),
                    "start_time_unix_nano": start_ns,
                    "start_time": _iso_timestamp(start_ns),
                    "end_time_unix_nano": end_ns,
                    "duration_ns": duration_ns,
                    "duration_ms": duration_ns / 1_000_000 if duration_ns else 0.0,
                    "status_code": _status_code(span, attributes),
                    "status_json": json.dumps(
                        span.get("status", {}),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    "attributes_json": json.dumps(
                        attributes, ensure_ascii=False, sort_keys=True
                    ),
                    "resource_attributes_json": json.dumps(
                        resource_attributes, ensure_ascii=False, sort_keys=True
                    ),
                    "scope_name": scope.get("name", ""),
                    "scope_version": scope.get("version", ""),
                    "trace_root_service_name": "",
                    "trace_root_span_name": "",
                    "source": "tempo",
                })
    root_spans = [row for row in rows if not row["parent_span_id"]]
    root_span = min(
        root_spans,
        key=lambda row: row["start_time_unix_nano"],
        default=None,
    )
    root_service_name = (
        root_span["service_name"] if root_span else ""
    ) or _search_root_value(search_trace.get("rootServiceName"))
    root_span_name = (
        root_span["span_name"] if root_span else ""
    ) or _search_root_value(search_trace.get("rootTraceName"))
    for row in rows:
        if not row["service_name"]:
            row["service_name"] = root_service_name
        row["trace_root_service_name"] = root_service_name
        row["trace_root_span_name"] = root_span_name
    if start is not None and end is not None:
        rows = _filter_trace_window(rows, start, end)
    return rows


def _filter_trace_window(
    rows: list[dict[str, Any]], start: datetime, end: datetime
) -> list[dict[str, Any]]:
    start_ns = _datetime_unix_nanos(start)
    end_ns = _datetime_unix_nanos(end)
    if end_ns <= start_ns:
        return []

    children: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        parent_span_id = row["parent_span_id"]
        if parent_span_id:
            children.setdefault(parent_span_id, []).append(row)

    roots = [
        row
        for row in rows
        if not row["parent_span_id"]
        and row["span_id"]
        and start_ns <= row["start_time_unix_nano"] < end_ns
    ]
    included_span_ids = {row["span_id"] for row in roots}
    pending_parent_ids = list(included_span_ids)
    while pending_parent_ids:
        parent_span_id = pending_parent_ids.pop()
        for child in children.get(parent_span_id, []):
            span_id = child["span_id"]
            if (
                span_id
                and span_id not in included_span_ids
                and start_ns <= child["start_time_unix_nano"] < end_ns
            ):
                included_span_ids.add(span_id)
                pending_parent_ids.append(span_id)

    return [row for row in rows if row["span_id"] in included_span_ids]


def _datetime_unix_nanos(value: datetime) -> int:
    value = value.astimezone(UTC)
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    elapsed = value - epoch
    return (
        (elapsed.days * 86_400 + elapsed.seconds) * 1_000_000_000
        + elapsed.microseconds * 1_000
    )


def _normalize_trace_id(value: Any) -> str:
    raw = str(value or "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{1,32}", raw):
        return raw.lower().zfill(32)
    return raw


def _search_root_value(value: Any) -> str:
    raw = str(value or "").strip()
    return "" if raw == "<root span not yet received>" else raw


def _attributes(attributes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        str(item.get("key", "")): _attribute_value(item.get("value", {}))
        for item in attributes
        if item.get("key")
    }


def _attribute_value(value: dict[str, Any]) -> Any:
    for key in (
        "stringValue",
        "intValue",
        "boolValue",
        "doubleValue",
        "bytesValue",
        "arrayValue",
        "kvlistValue",
    ):
        if key in value:
            nested = value[key]
            if key == "bytesValue":
                return nested
            if key == "arrayValue":
                return [
                    _attribute_value(item)
                    for item in nested.get("values", [])
                ]
            if key == "kvlistValue":
                return _attributes(nested.get("values", []))
            return nested
    return None


def _decode_otel_id(value: Any) -> str:
    if not value:
        return ""
    raw = str(value)
    try:
        return base64.b64decode(raw, validate=True).hex()
    except (ValueError, base64.binascii.Error):
        return raw


def _first_attribute(attributes: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = attributes.get(key)
        if value is not None:
            return str(value)
    return ""


def _status_code(span: dict[str, Any], attributes: dict[str, Any]) -> Any:
    for key in (
        "http.response.status_code",
        "http.status_code",
        "rpc.grpc.status_code",
    ):
        if key in attributes:
            return attributes[key]
    return span.get("status", {}).get("code", "")


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _search_bounds(start: datetime, end: datetime) -> tuple[int, int]:
    return int(start.timestamp()), math.ceil(end.timestamp())


def _iso_timestamp(timestamp_ns: int) -> str:
    if not timestamp_ns:
        return ""
    return datetime.fromtimestamp(
        timestamp_ns / 1_000_000_000, tz=UTC
    ).isoformat(timespec="microseconds")
