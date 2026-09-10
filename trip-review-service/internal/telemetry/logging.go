package telemetry

import (
	"context"
	"fmt"
	"log/slog"

	"go.opentelemetry.io/contrib/bridges/otelslog"
	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc"
	sdklog "go.opentelemetry.io/otel/sdk/log"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.34.0"
)

func NewLoggerProvider(
	ctx context.Context,
	serviceName string,
	environment string,
) (*sdklog.LoggerProvider, error) {
	exporter, err := otlploggrpc.New(ctx)
	if err != nil {
		return nil, fmt.Errorf("create OTLP log exporter: %w", err)
	}

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
		_ = exporter.Shutdown(ctx)
		return nil, fmt.Errorf("create log resource: %w", err)
	}

	return sdklog.NewLoggerProvider(
		sdklog.WithProcessor(sdklog.NewBatchProcessor(exporter)),
		sdklog.WithResource(serviceResource),
	), nil
}

func NewSlogLogger(
	instrumentationScope string,
	loggerProvider *sdklog.LoggerProvider,
) *slog.Logger {
	return slog.New(
		otelslog.NewHandler(
			instrumentationScope,
			otelslog.WithLoggerProvider(loggerProvider),
		),
	)
}
