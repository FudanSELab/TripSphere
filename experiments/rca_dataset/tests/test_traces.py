from datetime import UTC, datetime

from tripsphere_rca.collectors.traces import _flatten_trace, _search_bounds


def test_flatten_trace_preserves_span_relationships_and_ids():
    detail = {
        "batches": [{
            "resource": {
                "attributes": [{
                    "key": "service.name",
                    "value": {"stringValue": "trip-itinerary-planner"},
                }],
            },
            "scopeSpans": [{
                "scope": {"name": "opentelemetry", "version": "1.0"},
                "spans": [
                    {
                        "spanId": "AQIDBAUGBwg=",
                        "startTimeUnixNano": "1000000000",
                        "endTimeUnixNano": "1250000000",
                        "name": "POST /plan",
                        "kind": "SPAN_KIND_SERVER",
                        "attributes": [{
                            "key": "http.request.method",
                            "value": {"stringValue": "POST"},
                        }],
                    },
                    {
                        "spanId": "CQoLDA0ODxA=",
                        "parentSpanId": "AQIDBAUGBwg=",
                        "startTimeUnixNano": "1050000000",
                        "endTimeUnixNano": "1150000000",
                        "name": "child",
                        "attributes": [],
                    },
                ],
            }],
        }],
    }

    rows = _flatten_trace(
        detail,
        "aabbcc",
        {
            "rootServiceName": "<root span not yet received>",
            "rootTraceName": "",
        },
        "case-1",
    )

    assert len(rows) == 2
    assert rows[0]["trace_id"] == "00000000000000000000000000aabbcc"
    assert rows[0]["span_id"] == "0102030405060708"
    assert rows[1]["span_id"] == "090a0b0c0d0e0f10"
    assert rows[1]["parent_span_id"] == "0102030405060708"
    assert rows[0]["service_name"] == "trip-itinerary-planner"
    assert rows[0]["trace_root_service_name"] == "trip-itinerary-planner"
    assert rows[0]["trace_root_span_name"] == "POST /plan"
    assert rows[0]["method_name"] == "POST"
    assert rows[0]["duration_ns"] == 250000000
    assert rows[1]["duration_ms"] == 100.0


def test_flatten_trace_keeps_only_in_window_connected_spans():
    detail = {
        "batches": [{
            "resource": {
                "attributes": [{
                    "key": "service.name",
                    "value": {"stringValue": "service-a"},
                }],
            },
            "scopeSpans": [{
                "scope": {},
                "spans": [
                    {
                        "spanId": "AQ==",
                        "startTimeUnixNano": "120000000000",
                        "endTimeUnixNano": "210000000000",
                        "name": "root",
                    },
                    {
                        "spanId": "Ag==",
                        "parentSpanId": "AQ==",
                        "startTimeUnixNano": "99000000000",
                        "endTimeUnixNano": "110000000000",
                        "name": "before-window",
                    },
                    {
                        "spanId": "Aw==",
                        "parentSpanId": "AQ==",
                        "startTimeUnixNano": "150000000000",
                        "endTimeUnixNano": "220000000000",
                        "name": "in-window",
                    },
                    {
                        "spanId": "BA==",
                        "parentSpanId": "AQ==",
                        "startTimeUnixNano": "200000000000",
                        "endTimeUnixNano": "210000000000",
                        "name": "at-window-end",
                    },
                ],
            }],
        }],
    }

    rows = _flatten_trace(
        detail,
        "aabbcc",
        {"rootServiceName": "service-a", "rootTraceName": "root"},
        "case-1",
        datetime.fromtimestamp(100, tz=UTC),
        datetime.fromtimestamp(200, tz=UTC),
    )

    assert [row["span_name"] for row in rows] == ["root", "in-window"]
    assert {row["span_id"] for row in rows} == {"01", "03"}
    assert all(
        100_000_000_000 <= row["start_time_unix_nano"] < 200_000_000_000
        for row in rows
    )


def test_search_bounds_round_end_up_to_avoid_zero_length_range():
    start = datetime.fromtimestamp(1000.90, tz=UTC)
    end = datetime.fromtimestamp(1000.95, tz=UTC)

    assert _search_bounds(start, end) == (1000, 1001)
