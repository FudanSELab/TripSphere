from __future__ import annotations

import json
import subprocess
from datetime import datetime

from tripsphere_rca.config import iso
from tripsphere_rca.faults.base import require_directory, require_positive
from tripsphere_rca.models import CaseSpec, InjectionResult


class DiskInjector:
    def __init__(self) -> None:
        self._active: InjectionResult | None = None

    def validate(self, case: CaseSpec) -> None:
        require_directory(case.fault.parameters["volume_path"], "volume_path")
        require_positive(int(case.fault.parameters.get("file_size_mb", 64)), "file_size_mb")
        require_positive(int(case.fault.parameters.get("rate_iops", 200)), "rate_iops")

    def start(self, case: CaseSpec) -> InjectionResult:
        params = case.fault.parameters
        volume = str(params["volume"])
        path = str(params["volume_path"])
        tool_path = str(params["tool_path"])
        size = int(params.get("file_size_mb", 64))
        iops = int(params.get("rate_iops", 200))
        timeout = case.workload.fault_seconds
        tool_container = str(params.get("tool_container", "tripsphere-fault-tools"))
        filename = f"{tool_path}/.tripsphere-disk-stress-{case.case_id}-{volume}.bin"
        command = ["docker", "exec", tool_container, "fio",
                   f"--name=tripsphere-{volume}", f"--filename={filename}",
                   f"--size={size}M", "--rw=randrw", "--rwmixread=50",
                   "--bs=4k", "--numjobs=2", f"--runtime={timeout}s",
                   "--time_based", "--direct=1", "--group_reporting",
                   f"--rate_iops={iops}", "--output-format=json", "--unlink=1"]
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        self._active = InjectionResult(
            fault_type=case.fault_type, target=volume, tool="fio",
            mode="predeployed_tool_container", command=command,
            started_at=iso(datetime.now().astimezone()),
            parameters={"volume": volume, "volume_path": path,
                        "file_size_mb": size, "rate_iops": iops,
                        "tool_container": tool_container,
                        "tool_path": tool_path},
            raw={"process": process},
        )
        return self._active

    def stop(self, case: CaseSpec) -> InjectionResult:
        if self._active is None:
            raise RuntimeError("disk injection is not active")
        return self.stop_result(case, self._active)

    def stop_result(self, case: CaseSpec, active: InjectionResult) -> InjectionResult:
        process = active.raw.get("process")
        if process is None:
            return active
        stdout, stderr = process.communicate(timeout=max(60, case.workload.fault_seconds + 30))
        try:
            fio = json.loads(stdout.strip()) if stdout.strip() else {}
        except json.JSONDecodeError:
            fio = {"raw_stdout": stdout}
        stopped = InjectionResult(
            fault_type=case.fault_type, target=case.fault.target, tool="fio",
            mode=active.mode, command=active.command,
            started_at=active.started_at,
            stopped_at=iso(datetime.now().astimezone()),
            returncode=process.returncode or 0, stdout=stdout, stderr=stderr,
            parameters=active.parameters, raw={"fio": fio},
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
