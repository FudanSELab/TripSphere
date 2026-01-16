# TripSphere

## Introduction

This monorepo contains the TripSphere, an AI-native distributed system based on microservices architecture.

## Quick Start

### Prerequisites

[Task](https://taskfile.dev/#/installation) is required to run the tasks defined in the `Taskfile.yml`. You can run `task` to show all available tasks.

We use [uv](https://docs.astral.sh/uv/) as the Python package and project manager. [Maven Wrapper](https://maven.apache.org/tools/wrapper/) is used to manage Java projects. [Go](https://go.dev/) should be installed for developing Golang projects. [Bun](https://bun.sh/) is used as the JavaScript runtime.

[Buf](https://buf.build/) needs to be installed to generate protobuf and gRPC codes.

### Protobuf and gRPC Codes

Protobuf and gRPC codes are useful to ensure projects can be compiled in development, and provide hints for IDEs. We use Buf to generate protobuf and gRPC codes. Run `task gen-proto` to generate protobuf and gRPC codes with Buf CLI.
