from __future__ import annotations

import shutil
from pathlib import Path

import requests

from tripsphere_rca.config import ROOT

ACTIVE_RULES_PATH = ROOT / "infra" / "prometheus" / "rules" / "active.yaml"


def activate_alert_rules(source: str | Path, prometheus_url: str) -> Path:
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = (ROOT / source_path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"alert rules file not found: {source_path}")

    ACTIVE_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = ACTIVE_RULES_PATH.with_suffix(".yaml.tmp")
    shutil.copyfile(source_path, temporary_path)
    temporary_path.replace(ACTIVE_RULES_PATH)

    try:
        response = requests.post(
            f"{prometheus_url.rstrip('/')}/-/reload",
            timeout=5,
        )
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout):
        # Prometheus may not be running yet; it will load active.yaml on startup.
        pass

    return source_path
