from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from tripsphere_rca.config import iso
from tripsphere_rca.faults.base import require_positive, run
from tripsphere_rca.models import CaseSpec, InjectionResult


class MemoryInjector:
    def __init__(self) -> None:
        self._active: InjectionResult | None = None

    def validate(self, case: CaseSpec) -> None:
        require_positive(int(case.fault.parameters.get("reserve_mb", 128)), "reserve_mb")
        require_positive(int(case.fault.parameters.get("rate_mb", 1)), "rate_mb")

    def start(self, case: CaseSpec) -> InjectionResult:
        target = case.fault.target
        reserve = int(case.fault.parameters.get("reserve_mb", 128))
        rate = int(case.fault.parameters.get("rate_mb", 1))
        tool = str(case.fault.parameters.get("tool_container", "chaosblade-tool"))
        blade_dir = str(case.fault.parameters.get("blade_dir", ""))
        run(["docker", "exec", "-u", "0", target, "rm", "-rf", "/tmp/chaosblade-1.8.1"])
        if blade_dir:
            run(["docker", "cp", blade_dir, f"{target}:/tmp/chaosblade-1.8.1"])
            source = blade_dir
        else:
            with tempfile.TemporaryDirectory(prefix="tripsphere-chaosblade-") as temp_dir:
                archive = str(Path(temp_dir) / "chaosblade")
                run(["docker", "cp", f"{tool}:/opt/chaosblade", archive])
                run(["docker", "cp", archive, f"{target}:/tmp/chaosblade-1.8.1"])
            source = f"{tool}:/opt/chaosblade"
        run(["docker", "exec", "-u", "0", target, "chmod", "+x",
             "/tmp/chaosblade-1.8.1/blade"])
        command = [
            "docker", "exec", "-u", "0", target, "/tmp/chaosblade-1.8.1/blade",
            "create", "mem", "load", "--mode", "ram", "--reserve", str(reserve),
            "--rate", str(rate), "--avoid-being-killed",
        ]
        result = run(command, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        if not payload.get("success") or not payload.get("result"):
            raise RuntimeError(f"ChaosBlade memory create failed: {payload}")
        self._active = InjectionResult(
            fault_type=case.fault_type, target=target, tool="ChaosBlade",
            mode="container_exec", uid=payload["result"], command=command,
            started_at=iso(datetime.now().astimezone()),
            parameters={"reserve_mb": reserve, "rate_mb": rate, "source": source},
            raw={"create_result": payload},
        )
        return self._active

    def stop(self, case: CaseSpec) -> InjectionResult:
        if self._active is None:
            raise RuntimeError("memory injection is not active")
        return self.stop_result(case, self._active)

    def stop_result(self, case: CaseSpec, active: InjectionResult) -> InjectionResult:
        command = [
            "docker", "exec", "-u", "0", case.fault.target,
            "/tmp/chaosblade-1.8.1/blade", "destroy", str(active.uid),
        ]
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
