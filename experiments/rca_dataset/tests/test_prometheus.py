import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from tripsphere_rca.collectors.prometheus import PrometheusCollector
from tripsphere_rca.models import CaseSpec, FaultSpec, TimeWindows


class FakePrometheusCollector(PrometheusCollector):
    def __init__(self):
        super().__init__("http://prometheus", step_seconds=15, chunk_seconds=60)
        self.calls = []

    def _get(self, path, params):
        self.calls.append((path, params))
        if path.endswith("metadata"):
            return {
                "status": "success",
                "data": {
                    "http_requests_total": [{
                        "type": "counter",
                        "help": "Requests",
                        "unit": "",
                    }]
                },
            }
        return {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {
                            "__name__": "http_requests_total",
                            "job": "api",
                            "instance": "api:8080",
                        },
                        "values": [
                            ["1000", "1"],
                            ["1015", "2"],
                        ],
                    },
                    {
                        "metric": {},
                        "values": [["1000", "3"]],
                    },
                ],
            },
        }


def test_full_series_are_deduplicated_and_keep_labels():
    tz = timezone.utc
    start = datetime.fromtimestamp(1000, tz)
    windows = TimeWindows(
        started=start,
        fault_started=start + timedelta(seconds=15),
        fault_stopped=start + timedelta(seconds=30),
        ended=start + timedelta(seconds=45),
    )
    case = CaseSpec(
        case_id="TEST",
        fault_category="Resource Fault",
        fault_type="CPU Hog",
        fault=FaultSpec(kind="cpu", target="api"),
    )

    frame, metadata = FakePrometheusCollector().collect(case, windows)

    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 2
    assert frame["metric_name"].notna().all()
    assert frame["metric_name"].ne("").all()
    assert set(frame["phase"]) == {"baseline", "fault"}
    assert '"job": "api"' in frame.iloc[0]["labels_json"]
    assert metadata["series_count"] == 1
    assert metadata["sample_count"] == 2
    assert metadata["status"] == "invalid"
    assert any("__name__" in error for error in metadata["errors"])


class FakeAlertPrometheusCollector(PrometheusCollector):
    def __init__(self):
        super().__init__("http://prometheus", step_seconds=15, chunk_seconds=60)

    def _get(self, path, params):
        assert path == "/api/v1/query_range"
        assert params["query"] == 'ALERTS{alertstate="firing"}'
        return {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {
                            "__name__": "ALERTS",
                            "alertname": "HttpServerErrorRateHigh",
                            "alertstate": "firing",
                            "severity": "critical",
                            "service": "trip-itinerary-planner",
                        },
                        "values": [
                            ["1000", "0"],
                            ["1015", "1"],
                            ["1030", "1"],
                            ["1045", "0"],
                        ],
                    },
                    {
                        "metric": {
                            "__name__": "ALERTS",
                            "alertname": "HttpServerLatencyHigh",
                            "alertstate": "firing",
                            "severity": "warning",
                            "service": "trip-itinerary-planner",
                        },
                        "values": [["1015", "1"], ["1030", "1"]],
                    },
                ],
            },
        }


def test_collect_alerts_returns_deduplicated_runtime_fields_without_annotations():
    tz = timezone.utc
    start = datetime.fromtimestamp(1000, tz)
    windows = TimeWindows(
        started=start,
        fault_started=start + timedelta(seconds=15),
        fault_stopped=start + timedelta(seconds=30),
        ended=start + timedelta(seconds=45),
    )

    alerts, errors = FakeAlertPrometheusCollector().collect_alerts(windows)

    assert errors == []
    assert len(alerts) == 2
    assert alerts[0]["labels"]["alertname"] == "HttpServerErrorRateHigh"
    assert alerts[0]["labels"]["service"] == "trip-itinerary-planner"
    assert alerts[0]["state"] == "resolved"
    assert alerts[0]["ends_at"] == "1970-01-01T00:17:25+00:00"
    assert "annotations" not in alerts[0]
    assert set(alerts[0]) == {"labels", "state", "starts_at", "ends_at", "value"}
    assert alerts[1]["state"] == "firing"
    assert alerts[1]["ends_at"] is None


def test_write_ticket_contains_only_monitor_based_fields(tmp_path):
    from tripsphere_rca.runner.case_runner import CaseRunner

    start = datetime(2026, 10, 14, 18, 40, 51, tzinfo=timezone.utc)
    windows = TimeWindows(
        started=start,
        fault_started=start + timedelta(seconds=15),
        fault_stopped=start + timedelta(seconds=30),
        ended=start + timedelta(seconds=45),
    )
    case = CaseSpec(
        case_id="TS-RCA-20261014-0001",
        fault_category="Resource Fault",
        fault_type="CPU Hog",
        fault=FaultSpec(kind="cpu", target="trip-itinerary-planner"),
        root=tmp_path,
    )
    alerts = [{
        "labels": {
            "alertname": "HttpServerErrorRateHigh",
            "severity": "critical",
            "service": "trip-itinerary-planner",
        },
        "state": "firing",
        "starts_at": "2026-10-14T18:41:00+00:00",
        "ends_at": None,
        "value": "0.18",
    }]

    CaseRunner._write_ticket(case, windows, alerts, [])
    payload = json.loads((case.case_dir / "ticket.json").read_text())

    assert payload["ticket_type"] == "monitor_based"
    assert payload["alerts"] == alerts
    assert "title" not in payload
    assert "annotations" not in payload
    assert "affected_entities" not in payload
    assert "fault_category" not in payload
    assert "fault_type" not in payload
