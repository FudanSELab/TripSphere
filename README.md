# TripSphere

## Overview

This monorepo contains the TripSphere, an AI-native distributed system based on microservices architecture.

## Motivation



## Deployment

### Docker Compose

```bash
docker compose -f deploy/docker-compose/docker-compose.yaml --env-file .env up --force-recreate --remove-orphans --detach
```

### Kubernetes

ONGOING

## Development

### Prerequisites

[Task](https://taskfile.dev/#/installation) is required to run the tasks defined in the `Taskfile.yml`. Run `task` to show all available tasks. [Buf](https://buf.build/) is required to generate protobuf and gRPC codes.

### Protobuf and gRPC Codes

Protobuf and gRPC codes are useful to ensure projects can be compiled, and provide hints for IDEs. We use Buf to generate protobuf and gRPC codes. Run `task gen-proto` to generate protobuf and gRPC codes with Buf CLI.

### Toolchain & Environment

- Bun 1.3.11 as JavaScript/TypeScript runtime and package manager
- `uv` as Python package and environment manager (Python 3.12.12)
- Maven Wrapper (`./mvnw`) as Java build and project manager (JDK 21)
- Go 1.25.6 as Golang runtime and package manager
