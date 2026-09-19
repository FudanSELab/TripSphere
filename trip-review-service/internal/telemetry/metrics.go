package telemetry

import (
	"context"
	"fmt"
	"runtime"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.34.0"
)

const (
	runtimeMeterName     = "trip-review-service/runtime"
	metricExportInterval = 15 * time.Second
	metricExportTimeout  = 5 * time.Second
	processMemoryUnit    = "By"
	processCPUThreadUnit = "{thread}"
)

func NewMeterProvider(
	ctx context.Context,
	serviceName string,
	environment string,
) (*sdkmetric.MeterProvider, error) {
	exporter, err := otlpmetricgrpc.New(ctx)
	if err != nil {
		return nil, fmt.Errorf("create OTLP metric exporter: %w", err)
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
		return nil, fmt.Errorf("create metric resource: %w", err)
	}

	provider := sdkmetric.NewMeterProvider(
		sdkmetric.WithReader(sdkmetric.NewPeriodicReader(
			exporter,
			sdkmetric.WithInterval(metricExportInterval),
			sdkmetric.WithTimeout(metricExportTimeout),
		)),
		sdkmetric.WithResource(serviceResource),
	)

	if err := registerRuntimeMetrics(provider.Meter(runtimeMeterName), serviceName, environment); err != nil {
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), metricExportTimeout)
		defer shutdownCancel()
		_ = provider.Shutdown(shutdownCtx)
		return nil, err
	}

	return provider, nil
}

func registerRuntimeMetrics(meter metric.Meter, serviceName string, environment string) error {
	commonAttributes := metric.WithAttributes(
		attribute.String("service.name", serviceName),
		attribute.String("service.namespace", serviceNamespace),
		attribute.String("deployment.environment.name", environment),
		attribute.String("runtime", "go"),
	)

	if _, err := meter.Int64ObservableGauge(
		"tripsphere.go.runtime.goroutines",
		metric.WithDescription("Current number of goroutines in the Go process."),
		metric.WithUnit("{goroutine}"),
		metric.WithInt64Callback(func(_ context.Context, observer metric.Int64Observer) error {
			observer.Observe(int64(runtime.NumGoroutine()), commonAttributes)
			return nil
		}),
	); err != nil {
		return fmt.Errorf("register goroutine metric: %w", err)
	}

	if _, err := meter.Int64ObservableGauge(
		"tripsphere.go.runtime.cpus",
		metric.WithDescription("Number of logical CPUs visible to the Go process."),
		metric.WithUnit(processCPUThreadUnit),
		metric.WithInt64Callback(func(_ context.Context, observer metric.Int64Observer) error {
			observer.Observe(int64(runtime.NumCPU()), commonAttributes)
			return nil
		}),
	); err != nil {
		return fmt.Errorf("register CPU count metric: %w", err)
	}

	if _, err := meter.Int64ObservableGauge(
		"tripsphere.go.process.memory.heap_alloc",
		metric.WithDescription("Bytes of allocated heap objects in the Go process."),
		metric.WithUnit(processMemoryUnit),
		metric.WithInt64Callback(func(_ context.Context, observer metric.Int64Observer) error {
			var stats runtime.MemStats
			runtime.ReadMemStats(&stats)
			observer.Observe(int64(stats.HeapAlloc), commonAttributes)
			return nil
		}),
	); err != nil {
		return fmt.Errorf("register heap allocation metric: %w", err)
	}

	if _, err := meter.Int64ObservableGauge(
		"tripsphere.go.process.memory.sys",
		metric.WithDescription("Bytes of memory obtained from the OS by the Go runtime."),
		metric.WithUnit(processMemoryUnit),
		metric.WithInt64Callback(func(_ context.Context, observer metric.Int64Observer) error {
			var stats runtime.MemStats
			runtime.ReadMemStats(&stats)
			observer.Observe(int64(stats.Sys), commonAttributes)
			return nil
		}),
	); err != nil {
		return fmt.Errorf("register runtime system memory metric: %w", err)
	}

	return nil
}
