First, synchronize the dependencies:

```shell
uv sync
```

Second, generate the gRPC code:

```shell
uv run -m grpc_tools.protoc \
    -Ilibs/proto \
    --python_out=libs/tripsphere/src \
    --grpc_python_out=libs/tripsphere/src \
    --mypy_out=libs/tripsphere/src \
    --mypy_grpc_out=libs/tripsphere/src \
    libs/proto/tripsphere/**/*.proto
```

Third, install the auto instrumentation:

```shell
uv run opentelemetry-bootstrap -a requirements | uv pip install --requirements -
```

Finally, start the server:

```shell
uv run -m itinerary.server
```