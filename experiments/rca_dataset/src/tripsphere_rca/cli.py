from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

from tripsphere_rca.config import ROOT
from tripsphere_rca.models import CaseSpec, CollectionSpec, FaultSpec, WorkloadSpec
from tripsphere_rca.runner.case_runner import CaseRunner
from tripsphere_rca.runner.inventory import refresh_inventory


def load_case(path: Path, alert_rules_override: Path | None = None) -> CaseSpec:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    run_mode = raw.get("run_mode", "fault")
    fault_raw = raw.get("fault", {})
    if run_mode == "baseline":
        fault_raw = {
            "kind": "none",
            "target": raw["target_service"],
            "tool": "",
            "parameters": {},
        }
    workload_raw = raw.get("workload", {})
    collection_raw = raw.get("collection", {})
    alert_rules = alert_rules_override or Path(
        collection_raw.get(
            "alert_rules", "infra/prometheus/rules/tripsphere-platform.yaml"
        )
    )
    if not alert_rules.is_absolute():
        alert_rules = (ROOT / alert_rules).resolve()
    collection_raw["alert_rules"] = str(alert_rules)
    parameters = dict(fault_raw.get("parameters", {}))
    if "volume_path" in parameters:
        volume_path = Path(str(parameters["volume_path"]))
        if not volume_path.is_absolute():
            parameters["volume_path"] = str((ROOT / volume_path).resolve())
    return CaseSpec(
        case_id=raw["case_id"],
        fault_category=raw.get(
            "fault_category",
            "No Fault" if run_mode == "baseline" else "Resource Fault",
        ),
        fault_type=raw.get(
            "fault_type", "No Fault" if run_mode == "baseline" else None
        ),
        fault=FaultSpec(
            kind=fault_raw["kind"],
            target=fault_raw["target"],
            tool=fault_raw.get("tool", ""),
            parameters=parameters,
        ),
        run_mode=run_mode,
        workload=WorkloadSpec(**workload_raw),
        collection=CollectionSpec(**collection_raw),
        root=ROOT,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="tripsphere-rca")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--spec", type=Path, required=True)
    run_parser.add_argument(
        "--alert-rules",
        type=Path,
        default=None,
        help="alert rules YAML to activate before running the case",
    )
    _add_inventory_options(run_parser)
    batch_parser = subparsers.add_parser("run-batch")
    batch_parser.add_argument("--dir", type=Path, required=True)
    batch_parser.add_argument(
        "--alert-rules",
        type=Path,
        default=None,
        help="alert rules YAML to activate before running the cases",
    )
    _add_inventory_options(batch_parser)
    args = parser.parse_args()
    if args.command == "run":
        if args.refresh_inventory:
            refresh_inventory(args.inventory_dsn, args.inventory_mode)
        result = CaseRunner().run(
            load_case(args.spec.resolve(), args.alert_rules)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result["status"] == "complete" else 1)
    if args.refresh_inventory:
        refresh_inventory(args.inventory_dsn, args.inventory_mode)
    specs = sorted(args.dir.glob("*.toml"))
    if not specs:
        raise SystemExit(f"no TOML case specs found in {args.dir}")
    results = []
    for spec in specs:
        result = CaseRunner().run(load_case(spec.resolve(), args.alert_rules))
        results.append(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["status"] != "complete":
            raise SystemExit(1)


def _add_inventory_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--refresh-inventory",
        action="store_true",
        help="regenerate the current inventory horizon and import it before running",
    )
    parser.add_argument(
        "--inventory-dsn",
        default=None,
        help="PostgreSQL DSN used by the inventory refresh",
    )
    parser.add_argument(
        "--inventory-mode",
        choices=("replace", "upsert", "insert_only"),
        default="replace",
        help="inventory import mode when refreshing",
    )
