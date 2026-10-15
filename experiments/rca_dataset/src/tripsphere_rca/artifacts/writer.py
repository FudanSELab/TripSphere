from __future__ import annotations

import json

from tripsphere_rca.config import iso
from tripsphere_rca.models import CaseSpec, InjectionResult, TimeWindows


def write_private_records(
    case: CaseSpec,
    windows: TimeWindows,
    injection: InjectionResult | None,
) -> None:
    ground_truth_dir = case.private_dir / "ground_truth"
    injection_dir = case.private_dir / "injection_records"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    injection_dir.mkdir(parents=True, exist_ok=True)
    ground_truth = {
        "case_id": case.case_id,
        "root_cause_entity": {
            "entity_id": f"svc:{case.fault.target}",
            "entity_type": "service",
            "name": case.fault.target,
        },
        "fault_category": case.fault_category,
        "fault_type": case.fault_type,
        "injection_tool": case.fault.tool,
        "fault_window": {
            "from": iso(windows.fault_started),
            "to": iso(windows.fault_stopped),
        },
        "parameters": case.fault.parameters,
    }
    (ground_truth_dir / f"{case.case_id}.json").write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    record = {
        "case_id": case.case_id,
        "fault_window": ground_truth["fault_window"],
        "injection": _safe_injection(injection),
    }
    (injection_dir / f"{case.case_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _safe_injection(value):
    if value is None:
        return None
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
