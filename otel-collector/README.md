Create a Docker network named `tripsphere` if it doesn't exist:

```bash
docker network create tripsphere
```

Run the OpenTelemetry Collector Docker container:

```bash
docker run -it --rm -p 4317:4317 -p 4318:4318 \
    -v ./otelcol-config.yaml:/etc/otelcol-config.yml \
    --network tripsphere \
    --name otel-collector \
    otel/opentelemetry-collector-contrib:0.86.0 \
    "--config=/etc/otelcol-config.yml"
```