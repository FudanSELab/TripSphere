Make sure you have installed [uv](https://docs.astral.sh/uv/) and [Task](https://taskfile.dev/).

Run `task install` to set up the development environment.

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

Finally, make sure MongoDB, Nacos, and Otel-collector are running. Start the server:

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