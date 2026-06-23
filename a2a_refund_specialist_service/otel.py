"""OpenTelemetry setup and helper utilities."""
from __future__ import annotations

import asyncio
import functools
import sys
from typing import Any

import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_otel(service_name: str) -> None:
    """Configure TracerProvider, MeterProvider, and auto-instrumentation."""
    resource = Resource.create({SERVICE_NAME: service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)


def instrument_fastapi(app) -> None:
    """Call after creating a FastAPI app to add automatic request tracing."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)


def function_trace(name: str | None = None):
    """Decorator: wrap a sync or async function in an OTel span."""
    def decorator(func):
        span_name = name or func.__qualname__
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with trace.get_tracer(func.__module__).start_as_current_span(span_name):
                    return await func(*args, **kwargs)
            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace.get_tracer(func.__module__).start_as_current_span(span_name):
                return func(*args, **kwargs)
        return sync_wrapper
    return decorator


def background_task(name: str, group: str = ""):
    """Decorator: create a root span for a background async task."""
    def decorator(func):
        span_name = f"{group}/{name}" if group else name

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with trace.get_tracer(func.__module__).start_as_current_span(span_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def set_attribute(key: str, value: Any) -> None:
    trace.get_current_span().set_attribute(key, value)


def add_event(event_name: str, attributes: dict[str, Any] | None = None) -> None:
    trace.get_current_span().add_event(event_name, attributes or {})


def notice_error() -> None:
    """Record the active exception on the current span."""
    exc = sys.exc_info()[1]
    if exc is not None:
        span = trace.get_current_span()
        span.record_exception(exc)
        span.set_status(trace.StatusCode.ERROR, str(exc))


_histograms: dict[str, Any] = {}


def record_metric(name: str, value: float) -> None:
    """Record a histogram observation (lazy-creates the instrument on first use)."""
    if name not in _histograms:
        _histograms[name] = metrics.get_meter(__name__).create_histogram(name)
    _histograms[name].record(value)
