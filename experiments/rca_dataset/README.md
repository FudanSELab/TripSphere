# TripSphere RCA Dataset

## Setup

```bash
cd experiments/rca_dataset
uv sync
buf registry login
buf generate
```

`buf generate` generates the ignored Python protobuf files from `contracts/protobuf`.

## Run

```bash
uv run tripsphere-rca run --spec configs/cases/cpu/order.toml
```

Collect a no-fault baseline with the same workload and telemetry collectors:

```bash
uv run tripsphere-rca run --spec configs/baselines/mixed-realistic.toml
```

Baseline cases set `run_mode = "baseline"`, skip fault injection, and store
all metric samples in the `baseline` phase.

Use the short-duration rules for a low-cost experiment:

```bash
uv run tripsphere-rca run \
  --alert-rules infra/prometheus/rules/tripsphere-platform-fast.yaml \
  --spec configs/cases/cpu/order.toml
```

The same option is available on `run-batch`. A case TOML can also set
`collection.alert_rules`; the CLI option takes precedence.

Refresh Inventory:

```bash
uv run --project experiments/rca_dataset   tripsphere-rca run   --refresh-inventory   --inventory-mode replace   --spec experiments/rca_dataset/configs/cases/cpu/planner.toml
```

```bash
uv run --project experiments/rca_dataset   tripsphere-rca run   --refresh-inventory   --inventory-mode replace  --alert-rules infra/prometheus/rules/tripsphere-platform-fast.yaml  --spec experiments/rca_dataset/configs/cases/cpu/planner.toml
```
