from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from tripsphere_rca.artifacts.manifest import write_artifacts
from tripsphere_rca.artifacts.writer import write_private_records
from tripsphere_rca.collectors.events import collect_events
from tripsphere_rca.collectors.logs import collect_logs
from tripsphere_rca.collectors.prometheus import PrometheusCollector
from tripsphere_rca.collectors.traces import TRACE_COLUMNS, collect_traces
from tripsphere_rca.collectors.workload import workload_summary
from tripsphere_rca.config import BUSINESS_SERVICES, SHANGHAI, iso
from tripsphere_rca.faults import create_injector
from tripsphere_rca.models import CaseSpec, InjectionResult, TimeWindows
from tripsphere_rca.runner.lifecycle import wait_seconds
from tripsphere_rca.runner.workload import start_workload, stop_workload


class CaseRunner:
    def run(self, case: CaseSpec) -> dict[str, Any]:
        self._validate_case(case)
        case.case_dir.mkdir(parents=True, exist_ok=True)
        injector = create_injector(case.fault.kind)
        injector.validate(case)
        self._wait_ready(case)
        started = datetime.now(SHANGHAI)
        workload = None
        active: InjectionResult | None = None
        stopped: InjectionResult | None = None
        errors: list[str] = []
        fault_started = started
        fault_stopped = started
        try:
            workload = start_workload(case)
            wait_seconds(case.workload.baseline_seconds)
            active = injector.start(case)
            fault_started = datetime.now(SHANGHAI)
            wait_seconds(case.workload.fault_seconds)
        except Exception as exc:
            errors.append(f"execution failed: {exc}")
        finally:
            if active is not None:
                try:
                    stopped = self._stop_injector(injector, case, active)
                    fault_stopped = datetime.now(SHANGHAI)
                    if stopped.returncode != 0:
                        errors.append(
                            f"fault cleanup returned {stopped.returncode}: {stopped.stderr}"
                        )
                except Exception as exc:
                    errors.append(f"fault stop failed: {exc}")
            try:
                injector.cleanup(case)
            except Exception as exc:
                errors.append(f"fault cleanup failed: {exc}")
            wait_seconds(case.workload.recovery_seconds)
            stop_workload(workload)
        ended = datetime.now(SHANGHAI)
        windows = TimeWindows(started, fault_started, fault_stopped, ended)
        counts = self._collect(case, windows, errors)
        workload_data = workload_summary(case.case_dir, case.fault.target)
        if not workload_data.get("request_count"):
            errors.append("workload produced no requests")
        write_private_records(case, windows, stopped or active)
        write_artifacts(
            case, windows, stopped or active,
            self._read_metric_metadata(case),
            workload_data,
            counts,
            errors,
        )
        return {
            "case_id": case.case_id,
            "status": "complete" if not errors else "invalid",
            "errors": errors,
            "case_dir": str(case.case_dir),
        }

    def _collect(self, case: CaseSpec, windows: TimeWindows, errors: list[str]) -> dict[str, int]:
        counts = {"metrics": 0, "logs": 0, "traces": 0, "events": 0}
        ticket_errors: list[str] = []
        collector = PrometheusCollector(
            case.collection.prometheus_url,
            case.collection.step_seconds,
            case.collection.chunk_seconds,
        )
        try:
            frame, metadata = collector.collect(case, windows)
            frame.to_parquet(case.case_dir / "metrics.parquet", index=False)
            (case.case_dir / "metric_metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            counts["metrics"] = len(frame)
            prometheus_errors = metadata.get("errors", [])
            errors.extend(prometheus_errors)
            ticket_errors.extend(prometheus_errors)
        except Exception as exc:
            error = f"metrics collection failed: {exc}"
            errors.append(error)
            ticket_errors.append(error)
            metadata = {"status": "invalid", "errors": [str(exc)]}
            self._empty_parquet(case.case_dir / "metrics.parquet", [
                "case_id", "query_name", "metric_name", "timestamp",
                "timestamp_unix_nano", "phase", "value", "labels_json",
                "series_id", "source",
            ])
            (case.case_dir / "metric_metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        try:
            counts["logs"] = collect_logs(
                case.collection.loki_url, case.case_id, BUSINESS_SERVICES,
                windows.started, windows.ended, case.case_dir / "logs.parquet",
            )
        except Exception as exc:
            errors.append(f"logs collection failed: {exc}")
            self._empty_parquet(case.case_dir / "logs.parquet", [
                "case_id", "service_name", "timestamp_ns", "line",
                "labels_json", "timestamp",
            ])
        try:
            counts["traces"] = collect_traces(
                case.collection.tempo_url, case.case_id,
                windows.started, windows.ended, case.case_dir / "traces.parquet",
            )
        except Exception as exc:
            errors.append(f"traces collection failed: {exc}")
            self._empty_parquet(case.case_dir / "traces.parquet", TRACE_COLUMNS)
        try:
            counts["events"] = collect_events(
                case.case_id, windows.started, windows.ended,
                case.case_dir / "events.parquet",
            )
        except Exception as exc:
            errors.append(f"events collection failed: {exc}")
            self._empty_parquet(case.case_dir / "events.parquet", [
                "case_id", "timestamp", "event_type", "source", "entity_id",
                "entity_type", "action", "status", "actor_id",
                "actor_attributes_json", "summary",
            ])
        alerts, alert_errors = collector.collect_alerts(windows)
        ticket_errors.extend(alert_errors)
        self._write_ticket(case, windows, alerts, ticket_errors)
        return counts

    @staticmethod
    def _stop_injector(injector, case, active):
        stop_result = getattr(injector, "stop_result", None)
        return stop_result(case, active) if stop_result else injector.stop(case)

    @staticmethod
    def _read_metric_metadata(case: CaseSpec) -> dict[str, Any]:
        path = case.case_dir / "metric_metadata.json"
        if not path.exists():
            return {"status": "invalid", "errors": ["metadata file missing"]}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_ticket(
        case: CaseSpec,
        windows: TimeWindows,
        alerts: list[dict[str, Any]],
        errors: list[str],
    ) -> None:
        payload = {
            "case_id": case.case_id,
            "ticket_type": "monitor_based",
            "created_at": iso(windows.fault_started),
            "time_window": {"from": iso(windows.started), "to": iso(windows.ended)},
            "alerts": alerts,
            "errors": errors,
        }
        case.case_dir.mkdir(parents=True, exist_ok=True)
        (case.case_dir / "ticket.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _empty_parquet(path, columns: list[str]) -> None:
        pd.DataFrame(columns=columns).to_parquet(path, index=False)

    @staticmethod
    def _validate_case(case: CaseSpec) -> None:
        if not case.case_id or not case.fault_type:
            raise ValueError("case_id and fault_type are required")
        if min(
            case.workload.baseline_seconds,
            case.workload.fault_seconds,
            case.workload.recovery_seconds,
        ) <= 0:
            raise ValueError("workload phase durations must be positive")

    @staticmethod
    def _wait_ready(case: CaseSpec) -> None:
        timeout_seconds = int(
            os.getenv("TRIPSPHERE_RCA_READY_TIMEOUT_SECONDS", "180")
        )
        endpoints = (
            ("Prometheus", f"{case.collection.prometheus_url}/-/ready"),
            ("Loki", f"{case.collection.loki_url}/ready"),
            ("Tempo", f"{case.collection.tempo_url}/ready"),
        )
        for service_name, url in endpoints:
            deadline = time.monotonic() + timeout_seconds
            last_status = "unreachable"
            last_body = ""
            while time.monotonic() < deadline:
                try:
                    response = requests.get(url, timeout=5)
                    last_status = str(response.status_code)
                    last_body = response.text.strip().replace("\n", " ")[:240]
                    if response.ok:
                        break
                except requests.RequestException as exc:
                    last_status = type(exc).__name__
                    last_body = str(exc)
                time.sleep(2)
            else:
                raise RuntimeError(
                    f"{service_name} is not ready after {timeout_seconds}s: "
                    f"{url} status={last_status} body={last_body}"
                )
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", case.fault.target],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or result.stdout.strip().lower() != "true":
            raise RuntimeError(f"target is not running: {case.fault.target}")
