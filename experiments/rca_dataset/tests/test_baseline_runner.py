import json
from datetime import UTC, datetime

import pandas as pd

from tripsphere_rca.artifacts.manifest import write_artifacts
from tripsphere_rca.models import CaseSpec, FaultSpec, TimeWindows, WorkloadSpec
from tripsphere_rca.runner.case_runner import CaseRunner


def test_baseline_validation_only_requires_baseline_duration():
    case = CaseSpec(
        case_id="BASELINE",
        fault_category="No Fault",
        fault_type="No Fault",
        fault=FaultSpec(kind="none", target="api"),
        run_mode="baseline",
        workload=WorkloadSpec(
            baseline_seconds=10,
            fault_seconds=0,
            recovery_seconds=0,
        ),
    )

    CaseRunner._validate_case(case)


def test_baseline_private_records_are_not_written(tmp_path):
    case = CaseSpec(
        case_id="BASELINE",
        fault_category="No Fault",
        fault_type="No Fault",
        fault=FaultSpec(kind="none", target="api"),
        run_mode="baseline",
        root=tmp_path,
    )
    windows = TimeWindows(
        datetime.now(UTC),
        datetime.now(UTC),
        datetime.now(UTC),
        datetime.now(UTC),
        "baseline",
    )

    from tripsphere_rca.artifacts.writer import write_private_records

    write_private_records(case, windows, None)

    assert not (case.private_dir / "ground_truth").exists()
    assert not (case.private_dir / "injection_records").exists()


def test_collection_writes_ticket_without_alerts(tmp_path, monkeypatch):
    case = CaseSpec(
        case_id="BASELINE",
        fault_category="No Fault",
        fault_type="No Fault",
        fault=FaultSpec(kind="none", target="api"),
        run_mode="baseline",
        root=tmp_path,
    )
    case.case_dir.mkdir(parents=True)
    started = datetime.now(UTC)
    windows = TimeWindows(started, started, started, started, "baseline")
    monkeypatch.setattr(
        "tripsphere_rca.runner.case_runner.PrometheusCollector.collect",
        lambda *_: (pd.DataFrame(), {"status": "complete", "errors": []}),
    )
    monkeypatch.setattr(
        "tripsphere_rca.runner.case_runner.collect_logs", lambda *args: 0
    )
    monkeypatch.setattr(
        "tripsphere_rca.runner.case_runner.collect_traces", lambda *args, **kwargs: 0
    )

    CaseRunner()._collect(case, windows, [])

    ticket = json.loads((case.case_dir / "ticket.json").read_text(encoding="utf-8"))
    assert ticket["case_id"] == case.public_case_id
    assert ticket["errors"] == []
    assert "alerts" not in ticket

    write_artifacts(
        case,
        windows,
        None,
        {"status": "complete", "errors": []},
        {},
        {"metrics": 0, "logs": 0, "traces": 0},
        [],
    )
    manifest = json.loads((case.case_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "ticket.json" in manifest["artifacts"]
