from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from tripsphere_rca.artifacts.topology import write_topology
from tripsphere_rca.config import iso
from tripsphere_rca.models import CaseSpec, InjectionResult, TimeWindows


def write_artifacts(
    case: CaseSpec,
    windows: TimeWindows,
    injection: InjectionResult | None,
    metrics_metadata: dict,
    workload: dict,
    counts: dict[str, int],
    errors: list[str],
) -> None:
    case.case_dir.mkdir(parents=True, exist_ok=True)
    (case.case_dir / "metric_metadata.json").write_text(
        json.dumps(metrics_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_topology(case)
    manifest = {
        "case_id": case.case_id,
        "runner_version": "0.1.0",
        "target_service": case.fault.target,
        "fault_category": case.fault_category,
        "fault_type": case.fault_type,
        "fault_spec": {
            "kind": case.fault.kind,
            "target": case.fault.target,
            "tool": case.fault.tool,
            "parameters": case.fault.parameters,
        },
        "workload_profile": case.workload.profile,
        "configured_phase_seconds": {
            "baseline": case.workload.baseline_seconds,
            "fault": case.workload.fault_seconds,
            "recovery": case.workload.recovery_seconds,
            "total": (
                case.workload.baseline_seconds
                + case.workload.fault_seconds
                + case.workload.recovery_seconds
            ),
        },
        "generated_at": iso(datetime.now().astimezone()),
        "time_window": {"from": iso(windows.started), "to": iso(windows.ended)},
        "baseline_window": {"from": iso(windows.started), "to": iso(windows.fault_started)},
        "fault_window": {"from": iso(windows.fault_started), "to": iso(windows.fault_stopped)},
        "recovery_window": {"from": iso(windows.fault_stopped), "to": iso(windows.ended)},
        "actual_phase_seconds": {
            "baseline": (windows.fault_started - windows.started).total_seconds(),
            "fault": (windows.fault_stopped - windows.fault_started).total_seconds(),
            "recovery": (windows.ended - windows.fault_stopped).total_seconds(),
            "total": (windows.ended - windows.started).total_seconds(),
        },
        "row_counts": counts,
        "trace_schema": "span-v1",
        "trace_row_semantics": "one row per span",
        "metric_series_count": metrics_metadata.get("series_count", 0),
        "metric_sample_count": metrics_metadata.get("sample_count", 0),
        "metric_collection_status": metrics_metadata.get("status", "invalid"),
        "metric_collection_errors": metrics_metadata.get("errors", []),
        "metric_collection_warnings": metrics_metadata.get("warnings", []),
        "business_load": workload,
        "injection": _json_safe(injection),
        "artifacts": [
            "metrics.parquet", "metric_metadata.json", "logs.parquet",
            "traces.parquet", "events.parquet", "ticket.json",
            "topology.json", "manifest.json", "locust.log",
            "locust_stats.csv", "locust_stats_history.csv",
            "locust_failures.csv", "locust_exceptions.csv",
        ],
        "status": "complete" if not errors else "invalid",
        "errors": errors,
    }
    (case.case_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _json_safe(value):
    if value is None:
        return None
    if isinstance(value, InjectionResult):
        return {
            "fault_type": value.fault_type,
            "target": value.target,
            "tool": value.tool,
            "mode": value.mode,
            "uid": value.uid,
            "command": value.command,
            "started_at": value.started_at,
            "stopped_at": value.stopped_at,
            "returncode": value.returncode,
            "stdout": value.stdout,
            "stderr": value.stderr,
            "parameters": value.parameters,
        }
    return value
