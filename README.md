# TripSphere

## Introduction

This monorepo contains the TripSphere, an AI-native distributed system based on microservices architecture.

## Quick Start

### Prerequisites

[Task](https://taskfile.dev/#/installation) is required to run the tasks defined in the `Taskfile.yml`. Run `task` to show all available tasks.

We use [uv](https://docs.astral.sh/uv/) as the Python package and project manager. [Maven Wrapper](https://maven.apache.org/tools/wrapper/) is used to manage Java projects. [Go](https://go.dev/) should be installed for developing Golang projects. [Bun](https://bun.sh/) is used as the JavaScript runtime.

Make sure [Buf](https://buf.build/) is installed if you want to generate protobuf codes without [Docker](https://www.docker.com/).

### Protobuf Codes

Protobuf codes are useful to ensure projects can be compiled in development, and provide hints for IDEs. We use [Buf](https://buf.build/) to generate protobuf codes. Run `task gen-protos` to generate protobuf codes.
