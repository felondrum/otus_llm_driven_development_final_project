"""gRPC stubs for Core Engine services."""

from chameleon.core.v1 import (
    common_pb2,
    orchestrator_pb2_grpc,
    retriever_pb2_grpc,
    llm_gateway_pb2_grpc,
)
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

# Алиасы для удобства
Empty = google_dot_protobuf_dot_empty__pb2.Empty

__all__ = [
    "common_pb2",
    "orchestrator_pb2_grpc",
    "retriever_pb2_grpc",
    "llm_gateway_pb2_grpc",
    "Empty",
]
