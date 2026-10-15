from __future__ import annotations

import time
from datetime import datetime

from tripsphere_rca.config import iso
from tripsphere_rca.models import CaseSpec, InjectionResult, TimeWindows


def wait_seconds(seconds: int) -> None:
    if seconds > 0:
        time.sleep(seconds)


def phase_windows(
    started: datetime,
    fault_started: datetime,
    fault_stopped: datetime,
    ended: datetime,
) -> TimeWindows:
    return TimeWindows(started, fault_started, fault_stopped, ended)


def result_to_dict(result: InjectionResult | None) -> dict:
    if result is None:
        return {}
    return {
        "fault_type": result.fault_type,
        "target": result.target,
        "tool": result.tool,
        "mode": result.mode,
        "uid": result.uid,
        "command": result.command,
        "started_at": result.started_at,
        "stopped_at": result.stopped_at,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parameters": result.parameters,
        "raw": result.raw,
    }
