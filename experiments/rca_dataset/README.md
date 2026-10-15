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

Refresh Inventory:

```bash
uv run --project experiments/rca_dataset   tripsphere-rca run   --refresh-inventory   --inventory-mode replace   --spec experiments/rca_dataset/configs/cases/cpu/planner.toml
```
