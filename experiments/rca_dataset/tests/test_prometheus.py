import json
from datetime import UTC, datetime, timedelta

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
                            "exported_job": "tripsphere/trip-review-service",
                        },
                        "values": [
                            ["1000", "1"],
                            ["1015", "2"],
                        ],
                    },
                    {
                        "metric": {
                            "__name__": "prometheus_http_requests_total",
                            "job": "prometheus",
                            "instance": "prometheus:9090",
                        },
                        "values": [["1000", "10"]],
                    },
                    {
                        "metric": {
                            "__name__": "container_cpu_usage_seconds_total",
                            "job": "cadvisor",
                            "container_label_com_docker_compose_service": "grafana",
                        },
                        "values": [["1000", "2"]],
                    },
                    {
                        "metric": {},
                        "values": [["1000", "3"]],
                    },
                ],
            },
        }


def test_full_series_are_deduplicated_without_labels_json():
    tz = UTC
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

    collector = FakePrometheusCollector()
    frame, metadata = collector.collect(case, windows)

    assert isinstance(frame, pd.DataFrame)
    assert collector.calls[0][1]["query"] == PrometheusCollector.series_query
    assert len(frame) == 2
    assert frame["metric_name"].notna().all()
    assert frame["metric_name"].ne("").all()
    assert set(frame["phase"]) == {"baseline", "fault"}
    assert frame["service_name"].tolist() == ["trip-review-service"] * 2
    assert "labels_json" not in frame.columns
    assert set(frame["metric_name"]) == {"http_requests_total"}
    assert metadata["series_count"] == 1
    assert metadata["sample_count"] == 2
    assert metadata["status"] == "invalid"
    assert any("__name__" in error for error in metadata["errors"])


def test_service_name_uses_service_label_before_exported_job():
    assert PrometheusCollector._service_name({
        "service_name": "trip-order-service",
        "exported_job": "tripsphere/trip-review-service",
    }) == "trip-order-service"
    assert PrometheusCollector._service_name({
        "exported_job": "tripsphere/trip-review-service",
    }) == "trip-review-service"
    assert PrometheusCollector._service_name({
        "job": "cadvisor",
        "container_label_com_docker_compose_service": "trip-review-service",
    }) == "trip-review-service"
    assert PrometheusCollector._service_name({
        "job": "java-services",
        "instance": "trip-itinerary-planner:8080",
    }) == "trip-itinerary-planner"
    assert PrometheusCollector._service_name({
        "job": "celery-exporter",
    }) == "trip-review-summary-worker"


def test_otel_application_metrics_get_service_name_and_hostmetrics_stay_unassigned():
    assert PrometheusCollector._service_name({
        "job": "otel-collector-exporter",
        "exported_job": "tripsphere/trip-chat-service",
    }) == "trip-chat-service"
    assert PrometheusCollector._service_name({
        "job": "otel-collector-exporter",
        "otel_scope_name": "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver/internal/scraper/cpuscraper",
    }) is None


def test_excludes_observability_and_its_cadvisor_metrics():
    assert PrometheusCollector._is_excluded_series({"job": "prometheus"})
    assert PrometheusCollector._is_excluded_series({"job": "node-exporter"})
    assert PrometheusCollector._is_excluded_series({
        "job": "cadvisor",
        "container_label_com_docker_compose_service": "loki",
    })
    assert not PrometheusCollector._is_excluded_series({
        "job": "cadvisor",
        "container_label_com_docker_compose_service": "trip-order-service",
    })
    assert not PrometheusCollector._is_excluded_series({
        "job": "otel-collector-exporter",
        "exported_job": "tripsphere/trip-order-service",
    })


def test_baseline_samples_are_all_marked_baseline():
    start = datetime.fromtimestamp(1000, tz=UTC)
    windows = TimeWindows(
        started=start,
        fault_started=start + timedelta(seconds=15),
        fault_stopped=start + timedelta(seconds=15),
        ended=start + timedelta(seconds=45),
        run_mode="baseline",
    )
    case = CaseSpec(
        case_id="BASELINE",
        fault_category="No Fault",
        fault_type="No Fault",
        fault=FaultSpec(kind="none", target="api"),
        run_mode="baseline",
    )

    frame, _ = FakePrometheusCollector().collect(case, windows)

    assert set(frame["phase"]) == {"baseline"}


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
    tz = UTC
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
    assert alerts[0]["ends_at"] == "1970-01-01T08:17:25.000000+08:00"
    assert "annotations" not in alerts[0]
    assert set(alerts[0]) == {"labels", "state", "starts_at", "ends_at", "value"}
    assert alerts[1]["state"] == "firing"
    assert alerts[1]["ends_at"] is None


def test_write_ticket_contains_only_monitor_based_fields(tmp_path):
    from tripsphere_rca.runner.case_runner import CaseRunner

    start = datetime(2026, 10, 14, 18, 40, 51, tzinfo=UTC)
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
    assert payload["case_id"] == case.public_case_id
    assert payload["time_window"]["from"] == "2026-10-15T02:40:51.000000+08:00"
    assert payload["alerts"] == alerts
    assert "title" not in payload
    assert "annotations" not in payload
    assert "affected_entities" not in payload
    assert "fault_category" not in payload
    assert "fault_type" not in payload
