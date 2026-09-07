package telemetry

import (
	"context"
	"fmt"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.34.0"
)

const serviceNamespace = "tripsphere"

func NewTracerProvider(
	ctx context.Context,
	serviceName string,
	environment string,
) (*sdktrace.TracerProvider, error) {
	exporter, err := otlptracegrpc.New(ctx)
	if err != nil {
		return nil, fmt.Errorf("create OTLP trace exporter: %w", err)
	}

	tracerProvider, err := newTracerProvider(ctx, exporter, serviceName, environment)
	if err != nil {
		if shutdownErr := exporter.Shutdown(ctx); shutdownErr != nil {
			return nil, fmt.Errorf("create trace resource: %w; shutdown exporter: %v", err, shutdownErr)
		}
		return nil, err
	}

	return tracerProvider, nil
}

func newTracerProvider(
	ctx context.Context,
	exporter sdktrace.SpanExporter,
	serviceName string,
	environment string,
) (*sdktrace.TracerProvider, error) {
	serviceResource, err := resource.New(
		ctx,
		resource.WithFromEnv(),
		resource.WithTelemetrySDK(),
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
			semconv.ServiceNamespace(serviceNamespace),
			semconv.DeploymentEnvironmentName(environment),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("create trace resource: %w", err)
	}

	return sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(serviceResource),
		sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.AlwaysSample())),
	), nil
}
