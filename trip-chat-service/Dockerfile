# First, build the application in the `/app` directory.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image.
ENV UV_PYTHON_DOWNLOADS=0

# Install the project into `/app`
WORKDIR /app

COPY libs ./libs

# Compile the gRPC Python files
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    # grpcio-tools version must match pyproject.toml
    uv run --locked --no-sync --with 'grpcio-tools>=1.75.1' \
    -m grpc_tools.protoc \
        -Ilibs/proto \
        --python_out=libs/tripsphere/src \
        --grpc_python_out=libs/tripsphere/src \
        libs/proto/tripsphere/**/*.proto

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from dependencies allows optimal layer caching
COPY pyproject.toml uv.lock README.md .
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Install OpenTelemetry auto instrumentation
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run --locked --no-dev opentelemetry-bootstrap -a requirements \
    | uv pip install --requirements -


# Then, use a final image without uv
FROM python:3.12-slim-bookworm
# It is important to use the image that matches the builder, 
# as the path to the Python executable must be the same, 
# e.g., using `python:3.11-slim-bookworm` will fail.

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set the OpenTelemetry environment variables
ENV OTEL_SERVICE_NAME="trip-chat-service" \
    OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317" \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true" \
    OTEL_PYTHON_LOG_LEVEL="info" \
    OTEL_PYTHON_LOG_CORRELATION="true"

# Use the non-root user to run our application
USER nonroot

# Use `/app` as the working directory
WORKDIR /app

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=24210

EXPOSE $UVICORN_PORT

# Start the instrumented app with default (FastAPI) arguments
ENTRYPOINT ["opentelemetry-instrument", "uvicorn", "chat.asgi:app"]
# Do NOT directly provide uvicorn `--port` option here.
# It must be overridden via environment variable.
# Otherwise, app may register incorrect port in service registry.
CMD []