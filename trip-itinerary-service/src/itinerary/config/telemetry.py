"""
OpenTelemetry automatic instrumentation setup for gRPC services.

This module provides zero-code-change distributed tracing using:
1. gRPC server auto-instrumentation
2. gRPC client auto-instrumentation (for calling other gRPC services)
3. MongoDB auto-instrumentation (if available)

All trace contexts are automatically propagated across service boundaries.
"""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_telemetry(
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
) -> None:
    """
    Configure OpenTelemetry with OTLP exporter and automatic instrumentation.

    This function sets up:
    1. OpenTelemetry TracerProvider with OTLP exporter
    2. gRPC server auto-instrumentation
    3. gRPC client auto-instrumentation
    4. MongoDB auto-instrumentation (if available)

    Args:
        service_name: Name of the service for trace identification
        otlp_endpoint: OTLP gRPC endpoint (default: http://otel-collector:4317)

    Environment Variables:
        SERVICE_NAME: Override service name
        OTLP_ENDPOINT: Override OTLP endpoint
        OTEL_TRACES_EXPORTER: Set to "none" to disable tracing
    """
    # Check if tracing is disabled
    if os.getenv("OTEL_TRACES_EXPORTER", "").lower() == "none":
        logger.info("OpenTelemetry tracing is disabled (OTEL_TRACES_EXPORTER=none)")
        return

    # Get configuration from environment or parameters
    service_name = service_name or os.getenv("SERVICE_NAME", "unknown-service")
    otlp_endpoint = otlp_endpoint or os.getenv(
        "OTLP_ENDPOINT", "http://otel-collector:4317"
    )

    logger.info(f"Initializing OpenTelemetry for service: {service_name}")

    # Create resource with service name
    resource = Resource.create({"service.name": service_name})

    # Set up the tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter to send traces to collector
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure for internal communication
    )

    # Add batch processor for efficient trace export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(f"✓ OpenTelemetry configured - sending traces to {otlp_endpoint}")

    # Auto-instrument gRPC server
    # This automatically extracts trace context from gRPC metadata
    GrpcInstrumentorServer().instrument()
    logger.info("✓ gRPC server auto-instrumentation enabled")

    # Auto-instrument gRPC client
    # This automatically propagates trace context in gRPC calls
    GrpcInstrumentorClient().instrument()
    logger.info("✓ gRPC client auto-instrumentation enabled")

    # Try to instrument MongoDB
    try:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

        PymongoInstrumentor().instrument()
        logger.info("✓ MongoDB auto-instrumentation enabled")
    except ImportError:
        logger.info("MongoDB instrumentation not available - skipping")
    except Exception as e:
        logger.warning(f"Failed to instrument MongoDB: {e}")
