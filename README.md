# TripSphere

## Introduction

This monorepo contains the TripSphere, an AI-native distributed system based on microservices architecture.

## Quick Start

### Prerequisites

[Task](https://taskfile.dev/#/installation) is required to run the tasks defined in the `Taskfile.yml`. Run `task` to show all available tasks.

[uv](https://docs.astral.sh/uv/) is used as Python package and project manager. [Maven Wrapper](https://maven.apache.org/tools/wrapper/) is used to manage Java projects. [Go](https://go.dev/) should be installed for developing in Golang projects. [Node.js](https://nodejs.org/en) is used as the JavaScript runtime.

### Protobuf Codes

Run `task copy-protos` to copy protobuf files from `contracts/protobuf` to service directories. Then change to the service directory, and run the tasks defined in `Taskfile.yaml` of each service to generate code from protobuf files.

Protobuf codes are useful to ensure projects can be compiled in development, and provide hints for IDEs.
