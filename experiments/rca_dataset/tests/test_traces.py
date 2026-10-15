from tripsphere_rca.collectors.traces import _flatten_trace


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
            "rootServiceName": "trip-itinerary-planner",
            "rootTraceName": "POST /plan",
        },
        "case-1",
    )

    assert len(rows) == 2
    assert rows[0]["trace_id"] == "aabbcc"
    assert rows[0]["span_id"] == "0102030405060708"
    assert rows[1]["span_id"] == "090a0b0c0d0e0f10"
    assert rows[1]["parent_span_id"] == "0102030405060708"
    assert rows[0]["service_name"] == "trip-itinerary-planner"
    assert rows[0]["method_name"] == "POST"
    assert rows[0]["duration_ns"] == 250000000
    assert rows[1]["duration_ms"] == 100.0
