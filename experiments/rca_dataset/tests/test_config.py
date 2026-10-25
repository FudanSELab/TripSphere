from datetime import datetime
from pathlib import Path

from tripsphere_rca.cli import load_case
from tripsphere_rca.config import SHANGHAI, iso


def test_case_specs_load_with_shared_workload():
    spec_root = Path(__file__).parents[1] / "configs" / "cases"
    cases = [
        load_case(path)
        for path in sorted(spec_root.glob("*/*.toml"))
    ]

    assert len(cases) >= 4
    assert {case.workload.profile for case in cases} == {
        "tripsphere_mixed_realistic_200rps"
    }
    assert {case.fault.kind for case in cases} == {
        "cpu", "memory", "socket", "disk"
    }
    disk_cases = [case for case in cases if case.fault.kind == "disk"]
    assert disk_cases
    assert all(Path(case.fault.parameters["volume_path"]).is_absolute()
               for case in disk_cases)


def test_alert_rules_override_is_resolved_from_repository_root():
    spec = Path(__file__).parents[1] / "configs" / "cases" / "cpu" / "order.toml"
    selected_rules = Path("infra/prometheus/rules/tripsphere-platform-fast.yaml")

    case = load_case(spec, selected_rules)

    assert case.collection.alert_rules.endswith(
        "infra/prometheus/rules/tripsphere-platform-fast.yaml"
    )


def test_public_case_id_is_stable_and_does_not_expose_case_semantics():
    spec = Path(__file__).parents[1] / "configs" / "cases" / "cpu" / "planner.toml"

    case = load_case(spec)

    assert case.public_case_id == "TS-RCA-CASE-5BB0D086D72F"
    assert "CPU" not in case.public_case_id
    assert "PLANNER" not in case.public_case_id
    assert case.case_dir.name == case.case_id


def test_iso_includes_microseconds():
    value = datetime(2026, 10, 15, 14, 15, 23, 123456, tzinfo=SHANGHAI)

    assert iso(value) == "2026-10-15T14:15:23.123456+08:00"


def test_baseline_case_has_no_fault_injection():
    spec = Path(__file__).parents[1] / "configs" / "baselines" / "mixed-realistic.toml"

    case = load_case(spec)

    assert case.run_mode == "baseline"
    assert case.fault.kind == "none"
    assert case.fault.target == "trip-order-service"
    assert case.fault_type == "No Fault"
    assert case.workload.fault_seconds == 0
    assert case.workload.recovery_seconds == 0
