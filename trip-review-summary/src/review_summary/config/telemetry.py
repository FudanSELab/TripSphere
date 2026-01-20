"""
OpenTelemetry automatic instrumentation setup.

This module provides zero-code-change distributed tracing using:
1. FastAPI auto-instrumentation (HTTP server)
2. httpx auto-instrumentation (HTTP client)
3. OpenLit auto-instrumentation (LangChain/LLM)
4. gRPC auto-instrumentation (gRPC client)
5. Neo4j auto-instrumentation (if available)
6. Qdrant auto-instrumentation (if available)

All trace contexts are automatically propagated across service boundaries
using W3C Trace Context standard (traceparent header).
"""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
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
    2. FastAPI auto-instrumentation
    3. httpx auto-instrumentation (for HTTP client calls)
    4. gRPC client auto-instrumentation
    5. OpenLit integration (if available, for LangChain/LLM tracing)
    6. Neo4j auto-instrumentation (if available)

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

    # Auto-instrument httpx for HTTP client calls
    # This automatically injects traceparent headers
    HTTPXClientInstrumentor().instrument()
    logger.info("✓ httpx auto-instrumentation enabled")

    # Auto-instrument gRPC client
    # This automatically propagates trace context in gRPC calls
    GrpcInstrumentorClient().instrument()
    logger.info("✓ gRPC client auto-instrumentation enabled")

    # Try to initialize OpenLit for LangChain/LLM tracing
    try:
        import openlit

        # Initialize OpenLit - it will automatically use the existing
        # OpenTelemetry TracerProvider we just configured
        openlit.init()
        logger.info("✓ OpenLit initialized for LangChain/LLM tracing")
    except ImportError:
        logger.info(
            "OpenLit not available - skipping LangChain/LLM instrumentation"
        )
    except Exception as e:
        logger.warning(f"Failed to initialize OpenLit: {e}")


def instrument_fastapi(app) -> None:
    """
    Instrument FastAPI application for automatic tracing.

    This should be called after creating the FastAPI app instance.
    It automatically:
    - Extracts trace context from incoming HTTP headers (W3C traceparent)
    - Creates spans for all HTTP requests
    - Injects trace context into the current request context

    Args:
        app: FastAPI application instance
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✓ FastAPI auto-instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")
