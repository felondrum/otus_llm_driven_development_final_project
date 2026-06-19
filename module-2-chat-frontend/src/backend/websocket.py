# ===========================================
# WebSocket handlers for Chat Frontend
# ===========================================

import asyncio
import json
import logging
import uuid
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from fastapi.websockets import WebSocket
import httpx

logger = logging.getLogger(__name__)

# Import gRPC client for Core Engine
try:
    from grpc_client.orchestrator_client import process_message
    logger.info("Successfully imported gRPC client for Core Engine")
except ImportError as e:
    logger.warning(f"Could not import gRPC client: {e}. Using fallback mode.")
    process_message = None


# Redis Pub/Sub for multi-container messaging
try:
    import redis.asyncio as redis
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
    
    redis_kwargs = {"host": REDIS_HOST, "port": REDIS_PORT, "decode_responses": True}
    if REDIS_PASSWORD:
        redis_kwargs["password"] = REDIS_PASSWORD
    
    redis_client = redis.Redis(**redis_kwargs)
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    REDIS_ENABLED = True
except ImportError:
    logger.warning("Redis not available, running in single-container mode")
    REDIS_ENABLED = False
    redis_client = None
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}. Running in single-container mode")
    REDIS_ENABLED = False
    redis_client = None


def generate_uuid_from_string(s: str) -> str:
    """Generate a deterministic UUID from a string."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


def get_container_id():
    """Get container ID from environment or generate a random one"""
    return os.environ.get("CHAT_INSTANCE", "unknown")


# List of test users (loaded from database)
from database import get_all_profiles, get_test_profiles

try:
    TEST_USERS = get_all_profiles()
    if not TEST_USERS:
        logger.info("No profiles in database, loading test profiles")
        TEST_USERS = get_test_profiles()
        # Insert test profiles into database
        from database import insert_profile
        for profile in TEST_USERS:
            insert_profile(profile)
except Exception as e:
    logger.warning(f"Failed to load profiles from database: {e}. Using test profiles.")
    TEST_USERS = get_test_profiles()


@dataclass
class Connection:
    """Represents a WebSocket connection"""
    websocket: WebSocket
    user_id: Optional[str] = None
    session_id: str = ""
    selected_recipient: Optional[str] = None
    container_id: str = "unknown"


class ConnectionManager:
    """Manages all WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[WebSocket, Connection] = {}
        self._session_counter = 0
        self.container_id = get_container_id()
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection and add to pool"""
        await websocket.accept()
        self._session_counter += 1
        connection = Connection(
            websocket=websocket,
            session_id=f"sess_{self._session_counter}",
            container_id=self.container_id
        )
        self.active_connections[websocket] = connection
        logger.info(f"New connection: {connection.session_id} (container: {self.container_id}). Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove connection from pool"""
        if websocket in self.active_connections:
            connection = self.active_connections[websocket]
            logger.info(f"Disconnecting: {connection.session_id}")
            del self.active_connections[websocket]
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to specific client"""
        try:
            logger.info(f"Sending message to {message.get('to')}: {message.get('text', '')[:50]}")
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast(self, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connections"""
        disconnected = []
        for websocket, connection in self.active_connections.items():
            if websocket == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection.session_id}: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            await self.disconnect(ws)
    
    def get_connection_by_user_id(self, user_id: str) -> Optional[Connection]:
        """Find connection by user_id"""
        for websocket, connection in self.active_connections.items():
            if connection.user_id == user_id:
                return connection
        return None
    
    async def publish_message(self, message: dict, recipient_user_id: str):
        """Publish message to Redis for other containers to receive"""
        if not REDIS_ENABLED or not redis_client:
            return
        
        try:
            channel = "chat_messages"
            await redis_client.publish(channel, json.dumps({
                "type": "message_route",
                "message": message,
                "recipient_user_id": recipient_user_id,
                "source_container": self.container_id
            }))
            logger.info(f"Published message to Redis for recipient {recipient_user_id}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
    
    async def send_to_recipient(self, message: dict, recipient_user_id: str, current_websocket: WebSocket):
        """Send message to recipient - local or via Redis if in different container"""
        recipient_connection = self.get_connection_by_user_id(recipient_user_id)
        
        logger.info(f"Attempting to send to recipient {recipient_user_id}, found connection: {recipient_connection is not None}")
        
        if recipient_connection:
            # Same container - send directly
            if recipient_connection.container_id == self.container_id:
                logger.info(f"Found local connection, sending to {recipient_user_id}")
                await self.send_message(recipient_connection.websocket, message)
                logger.info(f"Message routed locally from {message.get('from')} to {recipient_user_id}")
            else:
                # Different container - publish to Redis
                logger.info(f"Recipient in different container, publishing to Redis")
                await self.publish_message(message, recipient_user_id)
        else:
            # Recipient not found locally - may be in другой container
            # Publish to Redis hoping another container has the connection
            logger.info(f"Recipient {recipient_user_id} not found locally, publishing to Redis")
            await self.publish_message(message, recipient_user_id)


connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket event loop"""
    connection = connection_manager.active_connections.get(websocket)
    if not connection:
        return
    
    logger.info(f"Connection established: {connection.session_id}")
    
    # Send welcome message
    await connection_manager.send_message(websocket, {
        "type": "welcome",
        "message": "Welcome to Chameleon Chat!",
        "available_users": TEST_USERS
    })
    
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message based on type
            message_type = message.get("type", "")
            
            if message_type == "auth":
                await handle_auth(websocket, message, connection)
            elif message_type == "message":
                await handle_message(websocket, message, connection)
            elif message_type == "select_recipient":
                await handle_select_recipient(websocket, message, connection)
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON message received")
        await connection_manager.send_message(websocket, {
            "type": "error",
            "message": "Invalid JSON format"
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        raise


async def handle_auth(websocket: WebSocket, message: dict, connection: Connection):
    """Handle authentication message"""
    user_id = message.get("user_id")
    
    # Simple auth - just check if user_id exists in test users
    valid_users = [u["user_id"] for u in TEST_USERS]
    
    if user_id and user_id in valid_users:
        connection.user_id = user_id
        
        # Find user details
        user_details = next((u for u in TEST_USERS if u["user_id"] == user_id), None)
        
        await connection_manager.send_message(websocket, {
            "type": "auth_ok",
            "session_id": connection.session_id,
            "user_id": user_id,
            "user_name": user_details["full_name"] if user_details else user_id
        })
        
        logger.info(f"User authenticated: {user_id} ({connection.session_id})")
    else:
        await connection_manager.send_message(websocket, {
            "type": "error",
            "message": f"Invalid user_id. Available: {', '.join(valid_users)}"
        })


async def handle_select_recipient(websocket: WebSocket, message: dict, connection: Connection):
    """Handle recipient selection"""
    recipient_id = message.get("recipient_id")
    
    if recipient_id:
        # Prevent selecting self as recipient
        if recipient_id == connection.user_id:
            logger.warning(f"User {connection.user_id} attempted to select self as recipient, ignoring")
            await connection_manager.send_message(websocket, {
                "type": "error",
                "message": "Cannot select yourself as recipient"
            })
            return
        
        connection.selected_recipient = recipient_id
        
        # Find recipient details
        recipient = next((u for u in TEST_USERS if u["user_id"] == recipient_id), None)
        
        await connection_manager.send_message(websocket, {
            "type": "recipient_selected",
            "recipient_id": recipient_id,
            "recipient_name": recipient["full_name"] if recipient else recipient_id
        })
        
        logger.info(f"Recipient selected: {recipient_id} ({connection.session_id})")


async def save_message_to_history(message: dict, recipient_id: str):
    """Save message to chat history using REST API"""
    # Используем recipient_id из параметра, но ключ будет сформирован в api.py на основе from и to
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://127.0.0.1:8080/api/v1/messages/{recipient_id}",
                json=message,
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Message saved to history with {recipient_id}")
            else:
                logger.warning(f"Failed to save message: {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not save message to history: {e}")


async def handle_message(websocket: WebSocket, message: dict, connection: Connection):
    """Handle message sending"""
    if not connection.user_id:
        await connection_manager.send_message(websocket, {
            "type": "error",
            "message": "Please authenticate first"
        })
        return
    
    if not connection.selected_recipient:
        await connection_manager.send_message(websocket, {
            "type": "error",
            "message": "Please select a recipient first"
        })
        return
    
    text = message.get("text", "").strip()
    style = message.get("style", "")
    
    if not text:
        await connection_manager.send_message(websocket, {
            "type": "error",
            "message": "Message cannot be empty"
        })
        return
    
    # Create message object
    import time
    msg_id = f"msg_{int(time.time() * 1000)}"
    
    # Convert user IDs to UUIDs for Core Engine gRPC
    sender_uuid = generate_uuid_from_string(connection.user_id)
    recipient_uuid = generate_uuid_from_string(connection.selected_recipient)
    
    # Call Core Engine gRPC for message processing
    adapted_result = {
        "adapted_text": text,
        "was_adapted": False,
        "confidence": 1.0,
        "model_used": "",
        "processing_time_ms": 0,
        "rules_applied": [],
        "metadata": {
            "from_cache": False,
            "fallback_used": False,
            "fallback_reason": "",
            "tokens_prompt": 0,
            "tokens_completion": 0,
        }
    }
    
    if process_message:
        try:
            logger.info(f"Sending message to Core Engine: sender={connection.user_id} (UUID: {sender_uuid}), recipient={connection.selected_recipient} (UUID: {recipient_uuid}), style={style}")
            result = process_message(
                sender_id=sender_uuid,
                recipient_id=recipient_uuid,
                text=text,
                style_name=style if style else None,
                message_id=msg_id
            )
            adapted_result = result
            logger.info(f"Core Engine response: was_adapted={result['was_adapted']}, model={result['model_used']}")
        except Exception as e:
            logger.error(f"Error calling Core Engine: {e}. Using original text.")
    else:
        logger.info("gRPC client not available, using original text")
    
    # Build sender message
    sender_message = {
        "type": "message",
        "id": msg_id,
        "from": connection.user_id,
        "to": connection.selected_recipient,
        "text": text,
        "adapted_text": adapted_result["adapted_text"],
        "was_adapted": adapted_result["was_adapted"],
        "timestamp": "2024-01-15T10:00:00Z",
        "style": style,
        "model_used": adapted_result["model_used"],
        "confidence": adapted_result["confidence"],
        "processing_time_ms": adapted_result["processing_time_ms"]
    }
    
    # Send to sender
    await connection_manager.send_message(websocket, sender_message)
    
    # Сохраняем сообщение в историю для отправителя (он же получатель в контексте истории)
    await save_message_to_history(sender_message, connection.selected_recipient)
    
    # Build recipient message
    recipient_message = {
        "type": "message",
        "id": msg_id,
        "from": connection.user_id,
        "to": connection.selected_recipient,
        "text": text,
        "adapted_text": adapted_result["adapted_text"],
        "was_adapted": adapted_result["was_adapted"],
        "timestamp": "2024-01-15T10:00:00Z",
        "style": style,
        "model_used": adapted_result["model_used"],
        "confidence": adapted_result["confidence"],
        "processing_time_ms": adapted_result["processing_time_ms"]
    }
    
    # Send to recipient
    await connection_manager.send_to_recipient(recipient_message, connection.selected_recipient, websocket)
    
    logger.info(f"Message processed and sent from {connection.user_id} to {connection.selected_recipient}")


# Styles list (loaded from Core Engine)
STYLES = [
    {"id": "chekhov", "name": "Антон Чехов", "description": "Ироничный, меланхоличный"},
    {"id": "dovlatov", "name": "Сергей Довлатов", "description": "Самоирония, короткие фразы"},
    {"id": "pelevin", "name": "Виктор Пелевин", "description": "Постмодерн, сатира"},
    {"id": "ilfpetrov", "name": "Ильф и Петров", "description": "Юмор, сатира, остроумие"}
]


async def get_users():
    """Get list of test users"""
    return TEST_USERS


async def get_styles():
    """Get list of available styles"""
    return STYLES
