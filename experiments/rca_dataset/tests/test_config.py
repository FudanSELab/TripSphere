from pathlib import Path

from tripsphere_rca.cli import load_case


def test_case_specs_load_with_shared_workload():
    spec_root = Path(__file__).parents[1] / "configs" / "cases"
    cases = [
        load_case(path)
        for path in sorted(spec_root.glob("*/*.toml"))
    ]

    assert len(cases) >= 4
    assert {case.workload.profile for case in cases} == {
        "tripsphere_mixed_realistic_50rps"
    }
    assert {case.fault.kind for case in cases} == {
        "cpu", "memory", "socket", "disk"
    }
    disk_cases = [case for case in cases if case.fault.kind == "disk"]
    assert disk_cases
    assert all(Path(case.fault.parameters["volume_path"]).is_absolute()
               for case in disk_cases)
