from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Protocol

from tripsphere_rca.models import CaseSpec, InjectionResult


class FaultInjector(Protocol):
    def validate(self, case: CaseSpec) -> None: ...
    def start(self, case: CaseSpec) -> InjectionResult: ...
    def stop(self, case: CaseSpec) -> InjectionResult: ...
    def cleanup(self, case: CaseSpec) -> None: ...


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check)


def require_positive(value: int | float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def require_directory(value: str | Path, name: str) -> Path:
    path = Path(value)
    if not path.is_dir():
        raise ValueError(f"{name} does not exist: {path}")
    return path
