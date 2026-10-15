from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tripsphere_rca.config import ROOT


DEFAULT_INVENTORY_DSN = (
    "postgresql://postgres:fudanse@localhost:5432/inventory_db"
)


def refresh_inventory(
    dsn: str | None = None,
    mode: str = "replace",
) -> dict[str, object]:
    """Regenerate the current inventory horizon and import it into PostgreSQL."""
    inventory_project = ROOT / "infra" / "initializer"
    generator = inventory_project / "scripts" / "create_inventories.py"
    database_dsn = (
        dsn
        or os.getenv("TRIPSPHERE_RCA_INVENTORY_DSN")
        or os.getenv("INVENTORY_POSTGRES_DSN")
        or DEFAULT_INVENTORY_DSN
    )

    _run([
        "uv",
        "run",
        "--project",
        str(inventory_project),
        "python",
        str(generator),
    ], inventory_project)
    result = _run([
        "uv",
        "run",
        "--project",
        str(inventory_project),
        "python",
        "-m",
        "initializer.inventories",
        "--mode",
        mode,
        "--dsn",
        database_dsn,
    ], inventory_project)
    return {
        "mode": mode,
        "dsn": database_dsn,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
