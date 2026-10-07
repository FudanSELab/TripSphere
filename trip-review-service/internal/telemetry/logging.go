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

	"trip-review-service/internal/correlation"
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
	handler := otelslog.NewHandler(
		instrumentationScope,
		otelslog.WithLoggerProvider(loggerProvider),
	)
	return slog.New(
		correlationHandler{Handler: handler},
	)
}

type correlationHandler struct {
	slog.Handler
}

func (h correlationHandler) Handle(ctx context.Context, record slog.Record) error {
	if requestID := correlation.RequestID(ctx); requestID != "" {
		record.AddAttrs(slog.String("request_id", requestID))
	}
	return h.Handler.Handle(ctx, record)
}

func (h correlationHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	return correlationHandler{Handler: h.Handler.WithAttrs(attrs)}
}

func (h correlationHandler) WithGroup(name string) slog.Handler {
	return correlationHandler{Handler: h.Handler.WithGroup(name)}
}
