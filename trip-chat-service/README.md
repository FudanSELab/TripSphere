First, synchronize the dependencies:

```bash
uv sync  # Install dependencies and dev-dependencies
```

Second, generate the gRPC code:

```bash
uv run -m grpc_tools.protoc \
    -Ilibs/proto \
    --python_out=libs/tripsphere/src \
    --grpc_python_out=libs/tripsphere/src \
    --mypy_out=libs/tripsphere/src \
    --mypy_grpc_out=libs/tripsphere/src \
    libs/proto/tripsphere/**/*.proto
```

Third, install the auto instrumentation:

```bash
uv run opentelemetry-bootstrap -a requirements \
    | uv pip install --requirements -
```

Set the OpenTelemetry environment variables:

```bash
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
export OTEL_PYTHON_LOG_LEVEL="info"
export OTEL_PYTHON_LOG_CORRELATION="true"
```

Set the uvicorn environment variables:

```bash
export UVICORN_HOST="0.0.0.0"
export UVICORN_PORT="24210"
```

Finally, make sure MongoDB and Nacos are running and start the server:

```bash
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    --service_name trip-chat-service \
    --exporter_otlp_endpoint http://127.0.0.1:4317 \
    uvicorn chat.asgi:app
```

Note: As the app reads port from environment variable `UVICORN_PORT` to register with service discovery, do not run uvicorn with `--port` option directly. Otherwise, app may register with an incorrect port.