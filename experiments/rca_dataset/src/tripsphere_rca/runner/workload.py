from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

from tripsphere_rca.config import WORKLOAD_PROTO_ROOT, WORKLOAD_ROOT
from tripsphere_rca.models import CaseSpec


def start_workload(case: CaseSpec) -> subprocess.Popen[str]:
    output = case.case_dir
    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [
        str(WORKLOAD_ROOT), str(WORKLOAD_PROTO_ROOT), environment.get("PYTHONPATH"),
    ]))
    if case.workload.order_sku_id:
        environment["TRIPSPHERE_RCA_ORDER_SKU_ID"] = case.workload.order_sku_id
        environment["CPU_HOG_ORDER_SKU_ID"] = case.workload.order_sku_id
    if case.workload.order_date:
        environment["TRIPSPHERE_RCA_ORDER_DATE"] = case.workload.order_date
        environment["CPU_HOG_ORDER_DATE"] = case.workload.order_date
    log_handle = (output / "locust.log").open("w", encoding="utf-8")
    command = [
        "uv", "run", "--project", str(Path(WORKLOAD_ROOT)),
        "locust", "-f", str(WORKLOAD_ROOT / "locustfile.py"),
        "--headless", "-u", str(_total_users()),
        "-r", str(case.workload.spawn_rate),
        "--run-time", f"{case.workload.baseline_seconds + case.workload.fault_seconds + case.workload.recovery_seconds}s",
        "--csv", str(output / "locust"),
        "--html", str(output / "locust-report.html"),
    ]
    process = subprocess.Popen(
        command, stdout=log_handle, stderr=subprocess.STDOUT,
        text=True, env=environment, start_new_session=True,
    )
    log_handle.close()
    return process


def stop_workload(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGINT)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def _total_users() -> int:
    import sys

    if str(WORKLOAD_ROOT) not in sys.path:
        sys.path.insert(0, str(WORKLOAD_ROOT))
    from workload_config import RATES

    return sum(rate.users for rate in RATES.values())
