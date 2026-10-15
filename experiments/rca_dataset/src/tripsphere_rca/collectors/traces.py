from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
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


def collect_traces(
    url: str,
    case_id: str,
    start: datetime,
    end: datetime,
    path,
    query_service: str | None = None,
    chunk_seconds: int = 30,
    limit: int = 1000,
) -> int:
    traces: dict[str, dict[str, Any]] = {}
    current = start
    while current < end:
        chunk_end = min(current + timedelta(seconds=chunk_seconds), end)
        params = {
            "start": int(current.timestamp()),
            "end": int(chunk_end.timestamp()),
            "limit": limit,
        }
        if query_service:
            params["tags"] = f'service.name="{query_service}"'
        response = requests.get(
            f"{url.rstrip('/')}/api/search", params=params, timeout=(5, 120)
        )
        response.raise_for_status()
        for trace in response.json().get("traces", []):
            if trace.get("traceID"):
                traces[trace["traceID"]] = trace
        if chunk_end >= end:
            break
        current = chunk_end

    rows: list[dict[str, Any]] = []
    for trace_id, trace in sorted(
        traces.items(), key=lambda item: int(item[1].get("startTimeUnixNano", 0) or 0)
    ):
        detail_response = requests.get(
            f"{url.rstrip('/')}/api/traces/{trace_id}", timeout=(5, 120)
        )
        detail_response.raise_for_status()
        detail = detail_response.json() or trace
        rows.extend(_flatten_trace(detail, trace_id, trace, case_id))
    frame = pd.DataFrame(rows, columns=TRACE_COLUMNS)
    frame.to_parquet(path, index=False)
    return len(frame)


def _flatten_trace(
    detail: dict[str, Any],
    trace_id: str,
    search_trace: dict[str, Any],
    case_id: str,
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
                row_service_name = service_name or str(
                    search_trace.get("rootServiceName", "") or ""
                )
                span_name = str(span.get("name", "") or "")
                rows.append({
                    "case_id": case_id,
                    "trace_id": trace_id,
                    "span_id": _decode_otel_id(span.get("spanId")),
                    "parent_span_id": _decode_otel_id(span.get("parentSpanId")),
                    "service_name": row_service_name,
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
                    "trace_root_service_name": search_trace.get(
                        "rootServiceName", ""
                    ),
                    "trace_root_span_name": search_trace.get("rootTraceName", ""),
                    "source": "tempo",
                })
    return rows


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


def _iso_timestamp(timestamp_ns: int) -> str:
    if not timestamp_ns:
        return ""
    return datetime.fromtimestamp(
        timestamp_ns / 1_000_000_000, tz=timezone.utc
    ).isoformat()
