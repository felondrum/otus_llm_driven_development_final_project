# Langfuse интеграция

import os
from typing import Dict, Any, Optional
from langfuse import Langfuse
from common.logging import logger


# Global langfuse instance
_langfuse: Optional[Langfuse] = None
_current_trace_context: Optional[Any] = None
_current_span: Optional[Any] = None


def init_langfuse(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None,
):
    """Initialize Langfuse client."""
    global _langfuse

    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY", "local-key")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY", "local-secret")
    host = host or os.getenv("LANGFUSE_HOST", "http://localhost:5000")

    # In Langfuse v3, SDK automatically sends data via OTLP to langfuse-worker
    # which then writes to ClickHouse. No manual flush needed.
    # The SDK uses the public/secret keys to authenticate with the Langfuse API.
    _langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    logger.info(f"Langfuse initialized with host: {host}")

    # Setup OpenTelemetry exporter explicitly to ensure traces reach Langfuse worker
    # _setup_otel_exporter() - function removed, OTLP settings are configured in docker-compose

    # DO NOT override OTEL environment variables - they are already set in docker-compose
    # The worker listens on port 4317 for GRPC data
    # OTEL_EXPORTER_OTLP_ENDPOINT=http://langfuse-worker:4317 (set in docker-compose)
    # OTEL_EXPORTER_OTLP_PROTOCOL=grpc (set in docker-compose)

    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "not set")
    otel_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "not set")
    logger.info(
        f"OTLP exporter configured: endpoint={otel_endpoint}, protocol={otel_protocol}"
    )

    # Validate OTLP configuration
    if otel_endpoint == "not set" or otel_protocol == "not set":
        logger.error(
            "OTEL environment variables not set! Data will not reach Langfuse worker."
        )
        logger.error(
            "Please ensure OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_PROTOCOL are set in docker-compose"
        )

    return True


def init_langfuse_from_config(config):
    """Initialize Langfuse from config."""
    host = config.get("services.langfuse.host", "http://localhost:5000")
    enabled = config.get("services.langfuse.enabled", False)

    if not enabled:
        logger.info("Langfuse is disabled")
        return False

    return init_langfuse(host=host)


def get_langfuse():
    """Get global langfuse instance."""
    return _langfuse


def start_trace(
    trace_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Start a new trace using Langfuse v3 API.

    Returns a context manager that MUST be used with 'with' statement.
    Manual __enter__/__exit__ calls will NOT work properly in Langfuse v3.
    
    Usage:
        with start_trace("my-trace") as trace:
            # Do work
            # Trace is automatically ended when exiting the with block
    """
    logger.info(f"Starting Langfuse trace: {trace_name}")

    if _langfuse:
        # In Langfuse v3, start_as_current_span returns a context manager
        # It MUST be used with 'with' statement - manual __enter__/__exit__ won't work
        context = _langfuse.start_as_current_span(
            name=trace_name,
            input={"metadata": metadata} if metadata else None,
        )
        logger.info(f"Langfuse trace context created: {trace_name}")
        return context
    else:
        logger.warning("Langfuse not initialized")
        return None


def start_span(
    span_name: str,
    input: Optional[Dict[str, Any]] = None,
):
    """Start a new span using Langfuse v3 API.

    Returns a context manager that MUST be used with 'with' statement.
    Manual __enter__/__exit__ calls will NOT work properly in Langfuse v3.
    
    Usage:
        with start_span("my-span") as span:
            # Do work
            # Span is automatically ended when exiting the with block
    """
    logger.info(f"Starting Langfuse span: {span_name}")

    if _langfuse:
        try:
            # In Langfuse v3, start_as_current_span returns a context manager
            # It MUST be used with 'with' statement - manual __enter__/__exit__ won't work
            context = _langfuse.start_as_current_span(
                name=span_name, input=input
            )
            logger.info(f"Langfuse span context created: {span_name}")
            return context
        except Exception as e:
            logger.error(f"Failed to start span {span_name}: {e}")
            return None
    else:
        logger.warning("Langfuse not initialized")
        return None


def end_span(
    output: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    usage: Optional[Dict[str, int]] = None,
):
    """End current span.
    
    Note: In Langfuse v3, spans are automatically ended when exiting the context manager.
    This function is kept for backward compatibility but does nothing.
    """
    logger.warning("end_span() is deprecated in Langfuse v3. Use 'with start_span() as span' context manager instead.")
    # No-op - context manager handles span lifecycle automatically


def end_trace(
    output: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None
):
    """End current trace.
    
    Note: In Langfuse v3, traces are automatically ended when exiting the context manager.
    This function is kept for backward compatibility but does nothing.
    """
    logger.warning("end_trace() is deprecated in Langfuse v3. Use 'with start_trace() as trace' context manager instead.")
    # No-op - context manager handles trace lifecycle automatically


def log_generation(
    name: str,
    model: str,
    prompt: str,
    completion: str,
    usage: Optional[Dict[str, int]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Log a generation to Langfuse using Langfuse v3 API.
    
    In Langfuse v3, use start_as_current_generation to create a generation observation.
    The SDK automatically sends data via OTLP to langfuse-worker.
    
    Usage:
        with log_generation("name", "model", "prompt", "completion") as generation:
            # Generation is logged within this context
            # The generation observation is automatically ended when exiting
            pass
    """
    logger.info(f"Logging generation to Langfuse: {name}, model={model}")

    if _langfuse:
        try:
            # In Langfuse v3, use start_as_current_generation which returns a context manager
            # This context manager MUST be used with 'with' statement
            return _langfuse.start_as_current_generation(
                name=name,
                model=model,
                input=prompt,
                output=completion,
                usage_details=usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error(f"Failed to log generation to Langfuse: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    else:
        logger.warning(
            "Cannot log generation - Langfuse not initialized"
        )
        return None


def log_event(
    name: str,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Log an event to Langfuse using Langfuse v3 API.
    
    Events are logged directly to the current active span/trace.
    """
    logger.info(f"Logging event to Langfuse: {name}")

    if _langfuse:
        try:
            # In Langfuse v3, events are logged within a span context
            # We use start_as_current_span with 'with' statement
            with _langfuse.start_as_current_span(name="event-context") as span:
                # Log the event - in Langfuse v3, use span.log() with event name
                span.log(
                    name=name,
                    input=data or {},
                    metadata=metadata or {},
                )
                logger.info(f"Event logged to Langfuse: {name}")
        except Exception as e:
            logger.error(f"Failed to log event to Langfuse: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.warning("Cannot log event - Langfuse not initialized")
