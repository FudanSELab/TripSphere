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

Run all cases in a directory:

```bash
uv run tripsphere-rca run-batch --dir configs/cases/cpu
```
