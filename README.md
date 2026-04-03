# TripSphere

## Overview

This monorepo contains TripSphere, an AI-native distributed system based on microservices architecture. It simulates an online travel platform where AI agents collaborate with backend services to handle tasks such as itinerary planning, order processing, etc.

## Motivation

Agentic Systems are rapidly emerging as a new software paradigm, with LLMs serving as the core reasoning engine. While powerful, the inherent non-determinism of LLMs — hallucinations, tool-call failures, cascading errors — can undermine the reliability of the entire distributed system. Studying the resilience of such systems is therefore critical.

TripSphere is a full-stack AI-native application designed as a benchmark and testbed for Agentic System research. It is a living system comprising microservices and AI agents built with four languages (Java, Python, Go, TypeScript).

- **Stateful environment.** Business flows persist data across databases and caches; agent decisions are influenced by historical system state, not just the current prompt.
- **Cloud-native.** Microservices architecture with full containerization, container orchestration, and OpenTelemetry-based observability where distributed traces span HTTP/gRPC calls and agent execution.
- **Modern agentic stack.** Integrates MCP, A2A, AI gateway, agent memory, and other contemporary patterns to produce representative traces and trajectories.

## Deployment

### Docker Compose

#### 1. Environment Configuration

Copy the example environment file to `.env` file:

```bash
cp .env.example .env
```

Then, open and edit `.env` to set your environment variables.

#### 2. Build Docker Images

Backend services and agents depend on protobuf and gRPC codes generated from `.proto` files. So before building the Docker images, you need to generate those codes using [Buf](https://buf.build).

For example, if you want to build docker image for `trip-chat-service`, execute the following commands:

```bash
cd trip-chat-service
buf generate
docker build . -t tripsphere/trip-chat-service:latest
cd ..
```

NOTE: Running `buf generate` too frequently/simultaneously may trigger rate limit from Buf Schema Registry (BSR).

#### 3. Docker Compose Up

When all the service/agent images are built, you can start the system by running the following command:

```bash
docker compose -f deploy/docker-compose/docker-compose.yaml --env-file .env \
  up --force-recreate --remove-orphans --detach
```

After the system is started, you should be able to access `http://<host>:3000` to view the TripSphere frontend.

#### 4. Configure AI Gateway

First, access the Higress console `http://<host>:8001`. You will be prompted to set the admin password on first access.

Then, add an AI service provider. Go through "AI Gateway Config" -> "LLM Provider Management" -> "Create AI Service Provider". Select your LLM provider (OpenAI/OpenAI Compatible, Google Gemini, etc.) and enter the real API key and (optionally) a custom base URL.

After adding the provider, go through "AI Gateway Config" -> "AI Route Config" -> "Create AI Route". Map your path prefix, e.g. `/v1`, to the target provider you just configured. To verify the AI route, send a test request using the command below:

```bash
curl -sv http://<host>:28080/v1/chat/completions \
    -X POST \
    -H 'Content-Type: application/json' \
    -d \
      '{
        "model": "<model-name>",
        "messages": [
          {
            "role": "user",
            "content": "Hello!"
          }
        ]
      }'
```

You should see the response from the AI provider. All AI-enabled services connect to Higress at `http://higress:8080/v1` inside the Docker network.

### Kubernetes

Coming soon.

## Development

### Prerequisites

[Buf](https://buf.build/) is required to generate protobuf and gRPC codes. Optionally install [Task](https://taskfile.dev/#/installation) to run grouped tasks defined in `Taskfile.yaml`. You can run `task` to show all available tasks defined in each `Taskfile.yaml`.

### Protobuf and gRPC Codes

Protobuf and gRPC codes are useful to ensure projects can be compiled, and provide hints for IDEs. In each service directory that contains `buf.gen.yaml`, run `buf generate` to generate the codes.

### Toolchain & Environment

- Bun 1.3.11 as JavaScript/TypeScript runtime and package manager
- `uv` as Python package and environment manager (Python 3.12.12)
- Maven Wrapper (`./mvnw`) as Java build and project manager (JDK 21)
- Go 1.25.6 as Golang runtime and package manager
