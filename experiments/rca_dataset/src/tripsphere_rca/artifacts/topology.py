from __future__ import annotations

import json
from pathlib import Path

from tripsphere_rca.config import BUSINESS_SERVICES
from tripsphere_rca.models import CaseSpec


def write_topology(case: CaseSpec) -> None:
    target = case.fault.target
    nodes = [
        {"entity_id": f"svc:{target}", "entity_type": "service", "name": target},
        *[
            {"entity_id": f"svc:{name}", "entity_type": "service", "name": name}
            for name in BUSINESS_SERVICES if name != target
        ],
    ]
    payload = {
        "case_id": case.case_id,
        "nodes": nodes,
        "edges": [],
        "fault_target": target,
    }
    (case.case_dir / "topology.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
