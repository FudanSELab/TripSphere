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
                        "metric": {
                            "__name__": "system_cpu_utilization_ratio",
                            "job": "otel-collector-exporter",
                        },
                        "values": [["1000", "0.5"]],
                    },
                    {
                        "metric": {
                            "__name__": "ALERTS",
                            "alertname": "ContainerCpuUsageHigh",
                            "alertstate": "firing",
                            "name": "trip-chat-service",
                        },
                        "values": [["1000", "1"]],
                    },
                    {
                        "metric": {},
                        "values": [["1000", "3"]],
                    },
                ],
            },
        }


def test_metadata_queries_each_unique_metric_and_preserves_missing_entries():
    collector = FakePrometheusCollector()
    frame = pd.DataFrame({
        "metric_name": ["http_requests_total", "missing_metric", "http_requests_total"],
    })

    metadata = collector._metadata(frame)

    entries = {item["metric_name"]: item for item in metadata["metrics"]}
    assert entries["http_requests_total"] == {
        "metric_name": "http_requests_total",
        "type": "counter",
        "help": "Requests",
        "unit": "",
        "metadata_missing": False,
    }
    assert entries["missing_metric"] == {
        "metric_name": "missing_metric",
        "type": None,
        "help": None,
        "unit": None,
        "metadata_missing": True,
    }
    metadata_calls = [
        params
        for path, params in collector.calls
        if path == "/api/v1/metadata"
    ]
    assert metadata_calls == [
        {"metric": "http_requests_total"},
        {"metric": "missing_metric"},
    ]
    assert "limit" not in metadata_calls[0]


def test_metadata_request_failure_only_marks_one_metric_missing():
    class FailingMetadataCollector(FakePrometheusCollector):
        def _get(self, path, params):
            if path == "/api/v1/metadata" and params["metric"] == "http_requests_total":
                raise RuntimeError("metadata endpoint unavailable")
            if path == "/api/v1/metadata" and params["metric"] == "second_metric":
                return {
                    "status": "success",
                    "data": {
                        "second_metric": [{
                            "type": "gauge",
                            "help": "Second metric",
                            "unit": "seconds",
                        }],
                    },
                }
            return super()._get(path, params)

    collector = FailingMetadataCollector()
    frame = pd.DataFrame({
        "metric_name": ["http_requests_total", "second_metric"],
    })

    metadata = collector._metadata(frame)

    entries = {item["metric_name"]: item for item in metadata["metrics"]}
    assert entries["http_requests_total"] == {
        "metric_name": "http_requests_total",
        "type": None,
        "help": None,
        "unit": None,
        "metadata_missing": True,
    }
    assert entries["second_metric"]["type"] == "gauge"
    assert any(
        "metadata unavailable for http_requests_total" in warning
        for warning in collector.warnings
    )


def test_metadata_maps_histogram_suffixes_to_one_base_metric_query():
    collector = FakePrometheusCollector()
    frame = pd.DataFrame({
        "metric_name": [
            "http_requests_total_bucket",
            "http_requests_total_count",
            "http_requests_total_sum",
        ],
    })

    metadata = collector._metadata(frame)

    assert [item["metric_name"] for item in metadata["metrics"]] == [
        "http_requests_total_bucket",
        "http_requests_total_count",
        "http_requests_total_sum",
    ]
    assert all(item["type"] == "counter" for item in metadata["metrics"])
    metadata_calls = [
        params
        for path, params in collector.calls
        if path == "/api/v1/metadata"
    ]
    assert metadata_calls == [{"metric": "http_requests_total"}]


def test_metadata_query_name_only_maps_supported_suffixes():
    assert PrometheusCollector._metadata_query_name("latency_bucket") == "latency"
    assert PrometheusCollector._metadata_query_name("latency_count") == "latency"
    assert PrometheusCollector._metadata_query_name("latency_sum") == "latency"
    assert PrometheusCollector._metadata_query_name("requests_total") == "requests_total"


def test_metadata_uses_first_entry_without_repeating_metadata_list():
    class MultipleMetadataCollector(FakePrometheusCollector):
        def _get(self, path, params):
            if path == "/api/v1/metadata":
                return {
                    "status": "success",
                    "data": {
                        params["metric"]: [
                            {"type": "counter", "help": "First", "unit": ""},
                            {"type": "counter", "help": "Second", "unit": ""},
                        ],
                    },
                }
            return super()._get(path, params)

    collector = MultipleMetadataCollector()
    metadata = collector._metadata(pd.DataFrame({
        "metric_name": ["http_requests_total"],
    }))

    assert metadata["metrics"] == [{
        "metric_name": "http_requests_total",
        "type": "counter",
        "help": "First",
        "unit": "",
        "metadata_missing": False,
    }]


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
    assert set(frame["service_name"]) == {"trip-review-service"}
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
    assert PrometheusCollector._is_excluded_series({
        "job": "cadvisor",
        "container_label_com_docker_compose_service": "chaosblade-tool",
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
