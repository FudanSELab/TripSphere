from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkloadSpec:
    profile: str = "tripsphere_mixed_realistic_50rps"
    baseline_seconds: int = 180
    fault_seconds: int = 300
    recovery_seconds: int = 180
    spawn_rate: float = 20.0
    order_sku_id: str | None = None
    order_date: str | None = None


@dataclass(frozen=True)
class CollectionSpec:
    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"
    tempo_url: str = "http://localhost:3200"
    step_seconds: int = 15
    chunk_seconds: int = 60


@dataclass(frozen=True)
class FaultSpec:
    kind: str
    target: str
    tool: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    fault_category: str
    fault_type: str
    fault: FaultSpec
    workload: WorkloadSpec = field(default_factory=WorkloadSpec)
    collection: CollectionSpec = field(default_factory=CollectionSpec)
    root: Path = Path(".")

    @property
    def case_dir(self) -> Path:
        return self.root / "dataset" / "public" / "cases" / self.case_id

    @property
    def private_dir(self) -> Path:
        return self.root / "dataset" / "private"


@dataclass
class InjectionResult:
    fault_type: str
    target: str
    tool: str
    mode: str = ""
    uid: str | None = None
    command: list[str] | str = field(default_factory=list)
    started_at: str | None = None
    stopped_at: str | None = None
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeWindows:
    started: datetime
    fault_started: datetime
    fault_stopped: datetime
    ended: datetime
