from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

import pandas as pd

from tripsphere_rca.config import SHANGHAI, iso

EVENT_COLUMNS = [
    "case_id", "timestamp", "event_type", "source", "entity_id",
    "entity_type", "action", "status", "actor_id", "actor_attributes_json",
    "summary",
]
EVENT_ACTIONS = {
    "create", "start", "stop", "restart", "die", "kill", "destroy", "oom",
    "pause", "unpause", "update", "rename", "health_status: healthy",
    "health_status: unhealthy",
}


def collect_events(case_id: str, start: datetime, end: datetime, path) -> int:
    command = [
        "docker", "events", "--since", start.astimezone(timezone.utc).isoformat(),
        "--until", end.astimezone(timezone.utc).isoformat(),
        "--filter", "type=container", "--format", "{{json .}}",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    rows = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        action = event.get("Action") or event.get("status") or ""
        if action not in EVENT_ACTIONS:
            continue
        actor = event.get("Actor") or {}
        attributes = actor.get("Attributes") or {}
        name = attributes.get("name") or actor.get("ID", "")
        timestamp = datetime.fromtimestamp(
            float(event.get("timeNano", 0)) / 1_000_000_000, timezone.utc
        ).astimezone(SHANGHAI)
        rows.append({
            "case_id": case_id,
            "timestamp": iso(timestamp),
            "event_type": "container_health" if action.startswith("health_status") else "container_lifecycle",
            "source": "docker_events",
            "entity_id": f"container:{name}",
            "entity_type": "container",
            "action": action,
            "status": event.get("status", ""),
            "actor_id": actor.get("ID", ""),
            "actor_attributes_json": json.dumps(attributes, ensure_ascii=False),
            "summary": f"{name} {action}".strip(),
        })
    frame = pd.DataFrame(rows, columns=EVENT_COLUMNS)
    frame.to_parquet(path, index=False)
    return len(frame)
