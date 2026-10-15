from __future__ import annotations

import subprocess
from datetime import datetime

from tripsphere_rca.config import iso
from tripsphere_rca.faults.base import require_positive
from tripsphere_rca.models import CaseSpec, InjectionResult


class SocketInjector:
    def __init__(self) -> None:
        self._active: InjectionResult | None = None

    def validate(self, case: CaseSpec) -> None:
        require_positive(int(case.fault.parameters.get("workers", 8)), "workers")

    def start(self, case: CaseSpec) -> InjectionResult:
        workers = int(case.fault.parameters.get("workers", 8))
        timeout = int(case.fault.parameters.get(
            "timeout_seconds", case.workload.fault_seconds
        ))
        target = case.fault.target
        command = [
            "docker", "run", "--rm", "--network", f"container:{target}",
            "alpine:3.20", "sh", "-c",
            f"set -eu; apk add --no-cache stress-ng >/dev/null; "
            f"stress-ng --sock {workers} --timeout {timeout}s --metrics-brief",
        ]
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        self._active = InjectionResult(
            fault_type=case.fault_type, target=target, tool="stress-ng",
            mode="temporary_container", command=command,
            started_at=iso(datetime.now().astimezone()),
            parameters={"workers": workers, "timeout_seconds": timeout},
            raw={"process": process},
        )
        return self._active

    def stop(self, case: CaseSpec) -> InjectionResult:
        if self._active is None:
            raise RuntimeError("socket injection is not active")
        return self.stop_result(case, self._active)

    def stop_result(self, case: CaseSpec, active: InjectionResult) -> InjectionResult:
        process = active.raw.get("process")
        if process is None:
            return active
        stdout, stderr = process.communicate(timeout=60)
        stopped = InjectionResult(
            fault_type=case.fault_type, target=case.fault.target, tool="stress-ng",
            mode=active.mode, command=active.command,
            started_at=active.started_at,
            stopped_at=iso(datetime.now().astimezone()),
            returncode=process.returncode or 0, stdout=stdout, stderr=stderr,
            parameters=active.parameters,
        )
        self._active = None
        return stopped

    def cleanup(self, case: CaseSpec) -> None:
        if self._active is None:
            return
        process = self._active.raw.get("process")
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        self._active = None
