# TripSphere

## Overview

This monorepo contains the TripSphere, an AI-native distributed system based on microservices architecture.

## Motivation



## Deployment

### Docker Compose

#### 1. Environment Configuration
```bash
cp .env.example .env
```
Open `.env` and set every value.

#### 2. Building the Images

Several services generate gRPC stubs from `.proto` files during the Docker build using the [Buf CLI](https://buf.build).  Buf fetches dependencies from the Buf Schema Registry (`buf.build`).  Running many builds simultaneously triggers **Rate limit** from BSR.

Build each service image sequentially (from the repository root):

For each service, do:
```bash
buf generate
docker build . -t tripsphere/{service_name}:latest
```

#### Compose up

```bash
docker compose -f deploy/docker-compose/docker-compose.yaml --env-file .env up --force-recreate --remove-orphans --detach
```
#### Configuring AI Gateway

**1. Open the Higress console**

Navigate to http://localhost:8001
Default admin credentials: `admin / admin`

**2. Add an AI service provider**

- Go to **AI Gateway Config → LLM Provider Manage → Create AI Service Provider**
- Select your provider (OpenAI, DeepSeek, Qwen, etc.)
- Enter the real API key and (optionally) a custom base URL

**3. Create a route**

- Go to **AI Gateway Config → AI Route Config → Create AI Route**
- Map path prefix `/v1` to the provider you just configured

**4. Verify**

All AI-enabled services (`trip-chat-service`, `trip-itinerary-planner`,
`trip-order-assistant`, `trip-review-summary`, `trip-review-summary-worker`)
connect to Higress at `http://higress:8080/v1` inside the Docker network.
No restart is required after updating Higress routes.


### Kubernetes

ONGOING

## Development

### Prerequisites

[Buf](https://buf.build/) is required to generate protobuf and gRPC codes. Optionally install [Task](https://taskfile.dev/#/installation) to run grouped tasks from `Taskfile.yaml` (`task` lists them).

### Protobuf and gRPC Codes

Protobuf and gRPC codes are useful to ensure projects can be compiled, and provide hints for IDEs. In each service directory that contains Buf config, run `buf generate` (see the loop under **Docker Compose → Building the Images** for the full list of directories).

### Toolchain & Environment

- Bun 1.3.11 as JavaScript/TypeScript runtime and package manager
- `uv` as Python package and environment manager (Python 3.12.12)
- Maven Wrapper (`./mvnw`) as Java build and project manager (JDK 21)
- Go 1.25.6 as Golang runtime and package manager
