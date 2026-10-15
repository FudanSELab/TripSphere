from pathlib import Path

import tripsphere_rca.runner.inventory as inventory


def test_refresh_inventory_runs_generator_then_importer(monkeypatch):
    calls = []

    def fake_run(command, cwd):
        calls.append((command, cwd))
        return inventory.subprocess.CompletedProcess(
            command, 0, stdout="ok", stderr=""
        )

    monkeypatch.setattr(inventory, "_run", fake_run)
    result = inventory.refresh_inventory(
        "postgresql://example/inventory",
        mode="upsert",
    )

    assert result["mode"] == "upsert"
    assert len(calls) == 2
    assert calls[0][0][0:3] == [
        "uv", "run", "--project"
    ]
    assert calls[1][0][-4:] == [
        "--mode", "upsert", "--dsn", "postgresql://example/inventory"
    ]
    assert all(isinstance(cwd, Path) for _, cwd in calls)
