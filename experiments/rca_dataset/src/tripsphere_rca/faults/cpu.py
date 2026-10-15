from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from tripsphere_rca.config import iso
from tripsphere_rca.faults.base import require_positive, run
from tripsphere_rca.models import CaseSpec, InjectionResult


class CpuInjector:
    def __init__(self) -> None:
        self._active: InjectionResult | None = None

    def validate(self, case: CaseSpec) -> None:
        require_positive(int(case.fault.parameters.get("cpu_percent", 80)), "cpu_percent")
        if int(case.fault.parameters.get("cpu_percent", 80)) > 100:
            raise ValueError("cpu_percent must be <= 100")

    def start(self, case: CaseSpec) -> InjectionResult:
        target = case.fault.target
        tool = str(case.fault.parameters.get("tool_container", "chaosblade-tool"))
        percent = int(case.fault.parameters.get("cpu_percent", 80))
        tar_file = str(case.fault.parameters.get("blade_tar_file", "/tmp/chaosblade.tar.gz"))
        target_id = run(["docker", "inspect", "--format", "{{.Id}}", target]).stdout.strip()
        command = [
            "docker", "exec", tool, "blade", "create", "docker", "cpu",
            "fullload", "--cpu-percent", str(percent), "--container-id", target_id,
            "--blade-tar-file", tar_file,
        ]
        result = run(command, check=False)
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            if not payload.get("success") or not payload.get("result"):
                raise RuntimeError(f"ChaosBlade did not create CPU experiment: {payload}")
            self._active = InjectionResult(
                fault_type=case.fault_type, target=target, tool="ChaosBlade",
                mode="docker", uid=payload["result"], command=command,
                started_at=iso(datetime.now().astimezone()),
                parameters={"cpu_percent": percent, "target_container_id": target_id},
                raw={"create_result": payload},
            )
            return self._active

        with tempfile.TemporaryDirectory(prefix="tripsphere-chaosblade-") as temp_dir:
            archive = str(Path(temp_dir) / "chaosblade")
            run(["docker", "cp", f"{tool}:/opt/chaosblade", archive])
            run(["docker", "exec", "-u", "0", target, "rm", "-rf", "/tmp/chaosblade"])
            run(["docker", "cp", archive, f"{target}:/tmp/chaosblade"])
        run(["docker", "exec", "-u", "0", target, "chmod", "+x", "/tmp/chaosblade/blade"])
        fallback = [
            "docker", "exec", "-u", "0", target, "/tmp/chaosblade/blade",
            "create", "cpu", "fullload", "--cpu-percent", str(percent),
        ]
        fallback_result = run(fallback, check=False)
        if fallback_result.returncode != 0:
            raise RuntimeError(fallback_result.stderr or fallback_result.stdout)
        payload = json.loads(fallback_result.stdout)
        if not payload.get("success") or not payload.get("result"):
            raise RuntimeError(f"ChaosBlade fallback failed: {payload}")
        self._active = InjectionResult(
            fault_type=case.fault_type, target=target, tool="ChaosBlade",
            mode="container_exec", uid=payload["result"], command=fallback,
            started_at=iso(datetime.now().astimezone()),
            parameters={"cpu_percent": percent, "target_container_id": target_id},
            raw={
                "create_result": {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                "fallback_result": payload,
            },
        )
        return self._active

    def stop(self, case: CaseSpec) -> InjectionResult:
        if self._active is None:
            raise RuntimeError("CPU injection is not active")
        return self.stop_result(case, self._active)

    def stop_result(self, case: CaseSpec, active: InjectionResult) -> InjectionResult:
        if not active.uid:
            raise RuntimeError("CPU injection has no uid")
        if active.mode == "container_exec":
            command = ["docker", "exec", "-u", "0", case.fault.target,
                       "/tmp/chaosblade/blade", "destroy", active.uid]
        else:
            command = ["docker", "exec", str(case.fault.parameters.get(
                "tool_container", "chaosblade-tool")), "blade", "destroy", active.uid]
        result = run(command, check=False)
        stopped = InjectionResult(
            fault_type=case.fault_type, target=case.fault.target, tool="ChaosBlade",
            mode=active.mode, uid=active.uid, command=command,
            started_at=active.started_at,
            stopped_at=iso(datetime.now().astimezone()),
            returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
            parameters=active.parameters, raw={"active": active.raw},
        )
        self._active = None
        return stopped

    def cleanup(self, case: CaseSpec) -> None:
        if self._active is not None:
            self.stop_result(case, self._active)
