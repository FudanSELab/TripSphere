from datetime import UTC, datetime

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
