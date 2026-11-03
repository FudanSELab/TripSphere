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

## Supported Fault Types

The current fault registry implements four fault types:

| Fault type | Injector | Cases | Direct collection status |
| --- | --- | ---: | --- |
| CPU Hog | ChaosBlade CPU | 3 | Ready to collect when the target services and telemetry stack are running. |
| Memory Leak | ChaosBlade Memory load | 4 | Ready to collect when the target services and telemetry stack are running. This injects controlled RAM pressure; it is not an application-code leak. |
| Socket Stress | `stress-ng` in a predeployed helper container per target | 3 | Ready after the prebuilt fault-tools helpers are deployed. |
| Disk I/O Stress | `fio` in a predeployed helper container | 3 | Ready after the prebuilt fault-tools helper is deployed and configured volume paths exist. |

The injector registry does not currently implement network delay, packet loss,
configuration faults, compatibility faults, component faults, or code-level
faults from the benchmark document. Those cases cannot be collected with the
current runner until an injector and case specification are added.

Build and start the tools image and helpers once before collecting Socket
Stress or Disk I/O Stress cases. It contains both tools; case execution does
not start helper containers, install packages, or access Alpine repositories.
Socket helpers share their target service's network namespace, while the disk
helper mounts the data root:

```bash
docker compose up -d --build \
  fault-tools \
  fault-tools-socket-chat \
  fault-tools-socket-order \
  fault-tools-socket-planner
```

Run one fault type at a time. Each `run-batch` is internally serial and stops
on the first invalid case. Do not run these batches concurrently with another
RCA batch, because they share the workload generator and telemetry backends.

From the repository root, run all currently supported fault cases serially:

```bash
set -euo pipefail

uv run --project experiments/rca_dataset \
  tripsphere-rca run-batch \
  --dir experiments/rca_dataset/configs/cases/cpu

uv run --project experiments/rca_dataset \
  tripsphere-rca run-batch \
  --dir experiments/rca_dataset/configs/cases/memory

uv run --project experiments/rca_dataset \
  tripsphere-rca run-batch \
  --dir experiments/rca_dataset/configs/cases/socket

uv run --project experiments/rca_dataset \
  tripsphere-rca run-batch \
  --dir experiments/rca_dataset/configs/cases/disk
```

Before starting the sequence, verify that the baseline or another fault run
is not still active. For disk cases, keep the configured database volume paths
available; `fio` writes a temporary test file under the mounted volume and
removes it when the case ends. If a target service is recreated, redeploy its
Socket helper so it rejoins the target's network namespace.

Refresh Inventory:

```bash
uv run --project experiments/rca_dataset   tripsphere-rca run   --refresh-inventory   --inventory-mode replace   --spec experiments/rca_dataset/configs/cases/cpu/planner.toml
```
