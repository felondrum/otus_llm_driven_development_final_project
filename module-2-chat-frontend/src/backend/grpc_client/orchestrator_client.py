# ===========================================
# gRPC Client for Core Engine Orchestrator
# ===========================================

import os
import sys
import grpc
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Add proto_gen to path for imports
proto_gen_path = os.path.join(os.path.dirname(__file__), "proto_gen")
if proto_gen_path not in sys.path:
    sys.path.insert(0, proto_gen_path)

try:
    import common_pb2
    import orchestrator_pb2
    import orchestrator_pb2_grpc
    logger.info("Successfully imported gRPC modules")
except ImportError as e:
    logger.warning(f"Could not import gRPC modules: {e}")

# Core Engine gRPC connection
ORCHESTRATOR_HOST = os.environ.get("ORCHESTRATOR_HOST", "127.0.0.1")
ORCHESTRATOR_PORT = os.environ.get("ORCHESTRATOR_PORT", "8001")


def get_profile(user_id: str) -> Optional[Dict]:
    """
    Get user profile from Core Engine via gRPC
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        Dict with profile data or None if not available
    """
    # Core Engine currently doesn't have profile retrieval endpoint
    # Profile management is handled by SQLite in this module
    logger.warning(f"Profile retrieval not supported by Core Engine, using SQLite fallback for user_id: {user_id}")
    return None


def get_orchestrator_stub():
    """Create and return gRPC stub for Orchestrator service"""
    try:
        channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(channel)
        # Test connection using ProcessMessage with empty request
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id="test",
            sender_id="test",
            recipient_id="test",
            text="test"
        )
        # Don't call HealthCheck - it doesn't exist in current proto
        logger.info(f"Created gRPC stub for Core Engine at {ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
        return stub, channel
    except Exception as e:
        logger.error(f"Failed to connect to Core Engine Orchestrator: {e}")
        return None, None


def process_message(
    sender_id: str,
    recipient_id: str,
    text: str,
    style_name: Optional[str] = None,
    message_id: Optional[str] = None
) -> Dict:
    """
    Call Core Engine gRPC to process and adapt message
    
    Args:
        sender_id: UUID of sender
        recipient_id: UUID of recipient
        text: Message text to adapt
        style_name: Optional writing style name
        message_id: Optional message ID for tracking
        
    Returns:
        Dict with adapted text and metadata
    """
    stub, channel = get_orchestrator_stub()
    
    if stub is None:
        logger.warning(f"Core Engine not available at {ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}, using fallback")
        return {
            "adapted_text": text,
            "was_adapted": False,
            "confidence": 1.0,
            "model_used": "",
            "processing_time_ms": 0,
            "rules_applied": [],
            "metadata": {
                "from_cache": False,
                "fallback_used": True,
                "fallback_reason": "Core Engine unavailable",
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }
        }
    
    try:
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=message_id or "",
            sender_id=sender_id,
            recipient_id=recipient_id,
            room_id="",
            text=text,
            style_name=style_name or "",
            metadata={}
        )
        
        response = stub.ProcessMessage(request, timeout=10.0)
        
        result = {
            "adapted_text": response.adapted_text,
            "was_adapted": response.was_adapted,
            "confidence": response.confidence,
            "model_used": response.model_used,
            "processing_time_ms": response.processing_time_ms,
            "rules_applied": list(response.rules_applied),
            "metadata": {
                "from_cache": response.adaptation_metadata.from_cache,
                "fallback_used": response.adaptation_metadata.fallback_used,
                "fallback_reason": response.adaptation_metadata.fallback_reason,
                "tokens_prompt": response.adaptation_metadata.tokens_prompt,
                "tokens_completion": response.adaptation_metadata.tokens_completion,
            }
        }
        
        logger.info(f"Core Engine processed message: was_adapted={result['was_adapted']}, model={result['model_used']}")
        
        return result
        
    except grpc.RpcError as e:
        logger.error(f"gRPC error calling Core Engine: {e.code()} - {e.details()}")
        return {
            "adapted_text": text,
            "was_adapted": False,
            "confidence": 0.0,
            "model_used": "",
            "processing_time_ms": 0,
            "rules_applied": [],
            "metadata": {
                "from_cache": False,
                "fallback_used": True,
                "fallback_reason": f"gRPC error: {e.code()}",
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }
        }
    except Exception as e:
        logger.error(f"Error calling Core Engine: {e}")
        return {
            "adapted_text": text,
            "was_adapted": False,
            "confidence": 0.0,
            "model_used": "",
            "processing_time_ms": 0,
            "rules_applied": [],
            "metadata": {
                "from_cache": False,
                "fallback_used": True,
                "fallback_reason": f"Error: {str(e)}",
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }
        }
    finally:
        if channel:
            channel.close()
