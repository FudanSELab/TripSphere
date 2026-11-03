from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests

from tripsphere_rca.config import iso
from tripsphere_rca.models import CaseSpec, TimeWindows


class PrometheusCollector:
    query_name = "prometheus_all_series"
    series_query = (
        '{__name__=~".+",job!~"^(loki|node-exporter|otel-collector-self|prometheus|tempo)$",'
        'container_label_com_docker_compose_service!~'
        '"^(cadvisor|chaosblade-tool|grafana|loki|otel-collector|prometheus|tempo)$"}'
    )
    excluded_scrape_jobs = {
        "loki", "node-exporter", "otel-collector-self", "prometheus", "tempo"
    }
    excluded_container_services = {
        "cadvisor",
        "chaosblade-tool",
        "grafana",
        "loki",
        "otel-collector",
        "prometheus",
        "tempo",
    }

    def __init__(self, url: str, step_seconds: int = 15, chunk_seconds: int = 60):
        self.url = url.rstrip("/")
        self.step_seconds = step_seconds
        self.chunk_seconds = chunk_seconds
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = requests.get(
                    f"{self.url}{path}", params=params, timeout=(5, 180)
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("status") != "success":
                    raise RuntimeError(payload.get("error", "Prometheus request failed"))
                return payload
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2**attempt)
        raise RuntimeError(f"Prometheus request failed: {path}") from last_error

    def collect(
        self, case: CaseSpec, windows: TimeWindows
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if self.step_seconds <= 0 or self.chunk_seconds <= 0:
            raise ValueError("Prometheus step and chunk must be positive")
        rows: dict[tuple[str, int], dict[str, Any]] = {}
        current = windows.started
        chunk = timedelta(seconds=self.chunk_seconds)
        while current < windows.ended:
            chunk_end = min(current + chunk, windows.ended)
            params = {
                "query": self.series_query,
                "start": current.timestamp(),
                "end": chunk_end.timestamp(),
                "step": self.step_seconds,
            }
            try:
                payload = self._get("/api/v1/query_range", params)
                for series in payload.get("data", {}).get("result", []):
                    labels = series.get("metric", {})
                    metric_name = labels.get("__name__")
                    if not metric_name:
                        self.errors.append("Prometheus returned a series without __name__")
                        continue
                    if metric_name in {"ALERTS", "ALERTS_FOR_STATE"}:
                        continue
                    if self._is_excluded_series(labels):
                        continue
                    service_name = self._service_name(labels)
                    if not service_name:
                        continue
                    series_id = self._series_id(labels)
                    for timestamp, value in series.get("values", []):
                        timestamp_ns = int(float(timestamp) * 1_000_000_000)
                        key = (series_id, timestamp_ns)
                        rows[key] = {
                            "case_id": case.public_case_id,
                            "query_name": self.query_name,
                            "metric_name": metric_name,
                            "service_name": service_name,
                            "timestamp": iso(datetime.fromtimestamp(
                                float(timestamp), windows.started.tzinfo
                            )),
                            "timestamp_unix_nano": timestamp_ns,
                            "phase": self._phase(
                                datetime.fromtimestamp(
                                    float(timestamp), windows.started.tzinfo
                                ),
                                windows,
                            ),
                            "value": float(value),
                            "series_id": series_id,
                            "source": "prometheus",
                        }
            except Exception as exc:
                self.errors.append(
                    f"chunk {current.isoformat()}..{chunk_end.isoformat()}: {exc}"
                )
            if chunk_end >= windows.ended:
                break
            current = chunk_end - timedelta(seconds=self.step_seconds)

        frame = pd.DataFrame(
            list(rows.values()),
            columns=[
                "case_id", "query_name", "metric_name", "timestamp",
                "timestamp_unix_nano", "phase", "value", "service_name",
                "series_id", "source",
            ],
        )
        if not frame.empty:
            frame = frame.sort_values(["timestamp_unix_nano", "series_id"])
        metadata = self._metadata(frame)
        metadata.update({
            "query": self.series_query,
            "step_seconds": self.step_seconds,
            "chunk_seconds": self.chunk_seconds,
            "series_count": int(frame["series_id"].nunique()) if not frame.empty else 0,
            "sample_count": len(frame),
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "invalid" if self.errors else "complete",
        })
        return frame, metadata

    @classmethod
    def _is_excluded_series(cls, labels: dict[str, str]) -> bool:
        if labels.get("job") in cls.excluded_scrape_jobs:
            return True
        container_service = labels.get("container_label_com_docker_compose_service")
        return (
            labels.get("job") == "cadvisor"
            and container_service in cls.excluded_container_services
        )

    @staticmethod
    def _service_name(labels: dict[str, str]) -> str | None:
        service_name = labels.get("service_name")
        if service_name:
            return service_name
        if labels.get("job") == "cadvisor":
            return labels.get("container_label_com_docker_compose_service") or None
        exported_job = labels.get("exported_job", "")
        prefix = "tripsphere/"
        if exported_job.startswith(prefix):
            return exported_job.removeprefix(prefix)
        if labels.get("job") == "java-services":
            instance = labels.get("instance", "")
            service = instance.rsplit(":", 1)[0]
            if service.startswith("trip-"):
                return service
        if labels.get("job") == "celery-exporter":
            return "trip-review-summary-worker"
        return None

    @staticmethod
    def _series_id(labels: dict[str, str]) -> str:
        serialized = json.dumps(labels, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _phase(timestamp: datetime, windows: TimeWindows) -> str:
        if windows.run_mode == "baseline":
            return "baseline"
        if timestamp < windows.fault_started:
            return "baseline"
        if timestamp < windows.fault_stopped:
            return "fault"
        return "recovery"

    def _metadata(self, frame: pd.DataFrame) -> dict[str, Any]:
        names = [] if frame.empty else sorted(frame["metric_name"].unique().tolist())
        query_names = sorted({self._metadata_query_name(name) for name in names})
        entries_by_name: dict[str, list[dict[str, Any]]] = {}
        for query_name in query_names:
            try:
                payload = self._get("/api/v1/metadata", {"metric": query_name})
                raw = payload.get("data", {})
                if not isinstance(raw, dict):
                    raise TypeError("metadata response data is not an object")
                entries = raw.get(query_name, [])
                if not isinstance(entries, list):
                    raise TypeError(f"metadata entries for {query_name} are not a list")
                entries_by_name[query_name] = entries
            except (requests.RequestException, RuntimeError, TypeError, ValueError) as exc:
                self.warnings.append(f"metadata unavailable for {query_name}: {exc}")
                entries_by_name[query_name] = []

        metadata: dict[str, Any] = {"metrics": []}
        for name in names:
            entries = entries_by_name[self._metadata_query_name(name)]
            first = entries[0] if entries else {}
            metadata["metrics"].append(
                {
                    "metric_name": name,
                    "type": first.get("type"),
                    "help": first.get("help"),
                    "unit": first.get("unit"),
                    "metadata_missing": not bool(entries),
                }
            )
        return metadata

    @staticmethod
    def _metadata_query_name(metric_name: str) -> str:
        for suffix in ("_bucket", "_count", "_sum"):
            if metric_name.endswith(suffix):
                return metric_name[: -len(suffix)]
        return metric_name
