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
    alerts_query = 'ALERTS{alertstate="firing"}'

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
                "query": '{__name__=~".+"}',
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
                    series_id = self._series_id(labels)
                    for timestamp, value in series.get("values", []):
                        timestamp_ns = int(float(timestamp) * 1_000_000_000)
                        key = (series_id, timestamp_ns)
                        rows[key] = {
                            "case_id": case.case_id,
                            "query_name": self.query_name,
                            "metric_name": metric_name,
                            "timestamp": datetime.fromtimestamp(
                                float(timestamp), windows.started.tzinfo
                            ).isoformat(),
                            "timestamp_unix_nano": timestamp_ns,
                            "phase": self._phase(
                                datetime.fromtimestamp(
                                    float(timestamp), windows.started.tzinfo
                                ),
                                windows,
                            ),
                            "value": float(value),
                            "labels_json": json.dumps(
                                labels, ensure_ascii=False, sort_keys=True
                            ),
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
                "timestamp_unix_nano", "phase", "value", "labels_json",
                "series_id", "source",
            ],
        )
        if not frame.empty:
            frame = frame.sort_values(["timestamp_unix_nano", "series_id"])
        metadata = self._metadata(frame)
        metadata.update({
            "query": '{__name__=~".+"}',
            "step_seconds": self.step_seconds,
            "chunk_seconds": self.chunk_seconds,
            "series_count": int(frame["series_id"].nunique()) if not frame.empty else 0,
            "sample_count": len(frame),
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "invalid" if self.errors else "complete",
        })
        return frame, metadata

    def collect_alerts(self, windows: TimeWindows) -> tuple[list[dict[str, Any]], list[str]]:
        alerts: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        current = windows.started
        chunk = timedelta(seconds=self.chunk_seconds)

        while current < windows.ended:
            chunk_end = min(current + chunk, windows.ended)
            params = {
                "query": self.alerts_query,
                "start": current.timestamp(),
                "end": chunk_end.timestamp(),
                "step": self.step_seconds,
            }
            try:
                payload = self._get("/api/v1/query_range", params)
                for series in payload.get("data", {}).get("result", []):
                    self._merge_alert_series(alerts, series)
            except Exception as exc:
                errors.append(
                    f"alert chunk {current.isoformat()}..{chunk_end.isoformat()}: {exc}"
                )
            if chunk_end >= windows.ended:
                break
            current = chunk_end - timedelta(seconds=self.step_seconds)

        return [
            finalized
            for alert in alerts.values()
            if (finalized := self._finalize_alert(alert, windows)) is not None
        ], errors

    def _merge_alert_series(
        self,
        alerts: dict[str, dict[str, Any]],
        series: dict[str, Any],
    ) -> None:
        labels = {
            key: value
            for key, value in series.get("metric", {}).items()
            if key not in {"__name__", "alertstate"}
        }
        alertname = series.get("metric", {}).get("alertname")
        if not alertname:
            return

        samples = [
            (float(timestamp), str(value))
            for timestamp, value in series.get("values", [])
        ]
        if not samples:
            return

        identity = json.dumps(labels, ensure_ascii=False, sort_keys=True)
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        alert = alerts.setdefault(
            key,
            {
                "labels": {"alertname": alertname, **labels},
                "samples": {},
            },
        )
        alert["samples"].update(dict(samples))

    def _finalize_alert(
        self,
        alert: dict[str, Any],
        windows: TimeWindows,
    ) -> dict[str, Any] | None:
        samples = sorted(alert["samples"].items())
        firing_samples = [
            (timestamp, value)
            for timestamp, value in samples
            if float(value) > 0
        ]
        if not firing_samples:
            return None

        first_timestamp = firing_samples[0][0]
        last_timestamp, last_value = samples[-1]
        last_sample_is_current = (
            float(last_value) > 0
            and last_timestamp >= windows.ended.timestamp() - self.step_seconds
        )
        ends_at = None
        state = "firing" if last_sample_is_current else "resolved"
        if not last_sample_is_current:
            last_firing_timestamp = firing_samples[-1][0]
            end_samples = [
                timestamp
                for timestamp, value in samples
                if timestamp > last_firing_timestamp and float(value) <= 0
            ]
            if end_samples:
                ends_at = datetime.fromtimestamp(
                    end_samples[0], windows.started.tzinfo
                ).isoformat()
            else:
                ends_at = datetime.fromtimestamp(
                    last_firing_timestamp, windows.started.tzinfo
                ).isoformat()

        return {
            "labels": alert["labels"],
            "state": state,
            "starts_at": datetime.fromtimestamp(
                first_timestamp, windows.started.tzinfo
            ).isoformat(),
            "ends_at": ends_at,
            "value": firing_samples[-1][1],
        }

    @staticmethod
    def _series_id(labels: dict[str, str]) -> str:
        serialized = json.dumps(labels, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _phase(timestamp: datetime, windows: TimeWindows) -> str:
        if timestamp < windows.fault_started:
            return "baseline"
        if timestamp < windows.fault_stopped:
            return "fault"
        return "recovery"

    def _metadata(self, frame: pd.DataFrame) -> dict[str, Any]:
        names = [] if frame.empty else sorted(frame["metric_name"].unique().tolist())
        metadata: dict[str, Any] = {"metrics": []}
        try:
            payload = self._get("/api/v1/metadata", {"limit": 0})
            raw = payload.get("data", {})
            for name in names:
                entries = raw.get(name, [])
                first = entries[0] if entries else {}
                metadata["metrics"].append({
                    "metric_name": name,
                    "type": first.get("type"),
                    "help": first.get("help"),
                    "unit": first.get("unit"),
                    "metadata": entries,
                    "metadata_missing": not bool(entries),
                })
        except Exception as exc:
            self.warnings.append(f"metadata unavailable: {exc}")
            metadata["metrics"] = [
                {
                    "metric_name": name,
                    "type": None,
                    "help": None,
                    "unit": None,
                    "metadata": [],
                    "metadata_missing": True,
                }
                for name in names
            ]
        return metadata
