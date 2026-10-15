from __future__ import annotations

import argparse
import os
from pathlib import Path

from tripsphere_rca.config import ROOT
from tripsphere_rca.models import CaseSpec, CollectionSpec, FaultSpec, WorkloadSpec
from tripsphere_rca.runner.case_runner import CaseRunner


CPU_TARGETS = {
    "trip-chat-service": "TS-RCA-CPU-HOG-CHAT",
    "trip-order-service": "TS-RCA-CPU-HOG-ORDER",
    "trip-itinerary-planner": "TS-RCA-CPU-HOG-PLANNER",
}

MEMORY_TARGETS = {
    "trip-chat-service": "TS-RCA-MEMORY-LEAK-CHAT",
    "trip-order-service": "TS-RCA-MEMORY-LEAK-ORDER",
    "trip-itinerary-planner": "TS-RCA-MEMORY-LEAK-PLANNER",
    "trip-review-summary": "TS-RCA-MEMORY-LEAK-REVIEW-SUMMARY",
}

SOCKET_TARGETS = {
    "trip-chat-service": "TS-RCA-SOCKET-STRESS-CHAT",
    "trip-order-service": "TS-RCA-SOCKET-STRESS-ORDER",
    "trip-itinerary-planner": "TS-RCA-SOCKET-STRESS-PLANNER-SSE",
}

DISK_VOLUMES = {
    "postgres": ("TS-RCA-DISK-IO-POSTGRES", "trip-order-service"),
    "mongodb": ("TS-RCA-DISK-IO-MONGODB", "trip-chat-service"),
    "redis": ("TS-RCA-DISK-IO-REDIS", "trip-chat-service"),
}


def main(kind: str) -> None:
    parser = _parser(kind)
    args = parser.parse_args()
    if kind == "cpu" and args.dry_run:
        print(_case(kind, args))
        return
    result = CaseRunner().run(_case(kind, args))
    print(result)
    raise SystemExit(0 if result["status"] == "complete" else 1)


def _parser(kind: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"legacy-{kind}-case",
        description="Compatibility wrapper for the unified TripSphere RCA runner.",
    )
    if kind == "disk":
        parser.add_argument("--volume", choices=sorted(DISK_VOLUMES), required=True)
    else:
        choices = {
            "cpu": sorted(CPU_TARGETS),
            "memory": sorted(MEMORY_TARGETS),
            "socket": sorted(SOCKET_TARGETS),
        }[kind]
        parser.add_argument("--target", choices=choices,
                            default=choices[0] if kind != "cpu" else "trip-chat-service")
    parser.add_argument("--baseline-seconds", type=int, default=180)
    parser.add_argument("--fault-seconds", type=int, default=300)
    parser.add_argument("--recovery-seconds", type=int, default=180)
    parser.add_argument("--spawn-rate", type=float, default=20)
    parser.add_argument("--order-sku-id",
                        default=os.getenv("TRIPSPHERE_RCA_ORDER_SKU_ID")
                        or os.getenv("CPU_HOG_ORDER_SKU_ID"))
    parser.add_argument("--order-date",
                        default=os.getenv("TRIPSPHERE_RCA_ORDER_DATE")
                        or os.getenv("CPU_HOG_ORDER_DATE"))
    if kind == "cpu":
        parser.add_argument("--cpu-percent", type=int, default=80)
        parser.add_argument("--tool-container", default="chaosblade-tool")
        parser.add_argument("--blade-tar-file", default="/tmp/chaosblade.tar.gz")
        parser.add_argument("--dry-run", action="store_true")
    elif kind == "memory":
        parser.add_argument("--reserve-mb", type=int, default=128)
        parser.add_argument("--rate-mb", type=int, default=1)
        parser.add_argument("--blade-dir", default="")
        parser.add_argument("--tool-container", default="chaosblade-tool")
    elif kind == "socket":
        parser.add_argument("--workers", type=int, default=8)
    else:
        parser.add_argument("--file-size-mb", type=int, default=64)
        parser.add_argument("--rate-iops", type=int, default=200)
    return parser


def _case(kind: str, args: argparse.Namespace) -> CaseSpec:
    if kind == "disk":
        case_id, target = DISK_VOLUMES[args.volume]
        parameters = {
            "volume": args.volume,
            "volume_path": str(ROOT / "volumes" / args.volume
                               if args.volume != "redis"
                               else ROOT / "volumes" / "redis" / "data"),
            "file_size_mb": args.file_size_mb,
            "rate_iops": args.rate_iops,
        }
        fault_type = "Disk I/O Stress"
        tool = "fio"
    else:
        target = args.target
        case_id = {
            "cpu": CPU_TARGETS,
            "memory": MEMORY_TARGETS,
            "socket": SOCKET_TARGETS,
        }[kind][target]
        parameters = {}
        fault_type = {
            "cpu": "CPU Hog",
            "memory": "Memory Leak",
            "socket": "Socket Stress",
        }[kind]
        tool = "chaosblade" if kind in {"cpu", "memory"} else "stress-ng"
        if kind == "cpu":
            parameters.update({
                "cpu_percent": args.cpu_percent,
                "tool_container": args.tool_container,
                "blade_tar_file": args.blade_tar_file,
            })
        elif kind == "memory":
            parameters.update({
                "reserve_mb": args.reserve_mb,
                "rate_mb": args.rate_mb,
                "blade_dir": args.blade_dir,
                "tool_container": args.tool_container,
            })
        else:
            parameters["workers"] = args.workers

    return CaseSpec(
        case_id=case_id,
        fault_category="Resource Fault",
        fault_type=fault_type,
        fault=FaultSpec(kind=kind, target=target, tool=tool, parameters=parameters),
        workload=WorkloadSpec(
            baseline_seconds=args.baseline_seconds,
            fault_seconds=args.fault_seconds,
            recovery_seconds=args.recovery_seconds,
            spawn_rate=args.spawn_rate,
            order_sku_id=args.order_sku_id,
            order_date=args.order_date,
        ),
        collection=CollectionSpec(),
        root=ROOT,
    )
