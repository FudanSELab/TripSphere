First, synchronize the dependencies:

```bash
uv sync
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
uv run opentelemetry-bootstrap -a requirements | uv pip install --requirements -
```

Set the OpenTelemetry environment variables:

```bash
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
export OTEL_PYTHON_LOG_LEVEL="info"
export OTEL_PYTHON_LOG_CORRELATION="true"
```

If you are using PowerShell:

```pwsh
$env:OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
$env:OTEL_PYTHON_LOG_LEVEL="info"
$env:OTEL_PYTHON_LOG_CORRELATION="true"
```

Start the MongoDB community server container:

```bash
docker run -d \
    -p 27017:27017 \
    --network tripsphere \
    --name mongodb \
    mongodb/mongodb-community-server:latest
```

Finally, start the server:

```bash
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    --service_name trip-chat-service \
    --exporter_otlp_endpoint http://127.0.0.1:4317 \
    python -m chat.server --nacos.server_address 127.0.0.1:8848
```

If you are using PowerShell:

```pwsh
uv run opentelemetry-instrument `
    --traces_exporter otlp `
    --metrics_exporter otlp `
    --logs_exporter otlp `
    --service_name trip-chat-service `
    --exporter_otlp_endpoint http://127.0.0.1:4317 `
    python -m chat.server --nacos.server_address 127.0.0.1:8848
```