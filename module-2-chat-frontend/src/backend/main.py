# ===========================================
# FastAPI server для Chat Frontend
# ===========================================

import asyncio
import os
import logging
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app FIRST (before importing modules that may use @app decorators)
app = FastAPI(
    title="Chameleon Chat API",
    description="WebSocket and REST API for Chameleon Chat system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import backend modules (same directory) - after app creation
from api import api_router
from websocket import websocket_endpoint, connection_manager, REDIS_ENABLED, redis_client, save_message_to_history

# Track Redis listener task
redis_listener_task = None


@app.on_event("startup")
async def startup_event():
    """Start Redis listener on startup if Redis is enabled"""
    global redis_listener_task
    if REDIS_ENABLED and redis_client and redis_listener_task is None:
        logger.info("Starting Redis Pub/Sub listener")
        redis_listener_task = asyncio.create_task(listen_to_redis())


async def listen_to_redis():
    """Listen to Redis Pub/Sub channel and broadcast to local WebSocket connections"""
    if not redis_client:
        return
    
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("chat_messages")
        logger.info("Subscribed to chat_messages channel")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    if data.get("type") == "message_route":
                        await handle_redis_message(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in Redis message")
                except Exception as e:
                    logger.error(f"Error handling Redis message: {e}")
    except Exception as e:
        logger.error(f"Redis listener error: {e}")


async def handle_redis_message(data: dict):
    """Handle message received from Redis (from another container)"""
    message = data.get("message", {})
    recipient_user_id = data.get("recipient_user_id")
    source_container = data.get("source_container")
    
    # Skip if message is from this container (message loop prevention)
    if source_container == connection_manager.container_id:
        logger.info(f"Skipping message from self (source: {source_container})")
        return
    
    # Find local connection for this recipient
    recipient_connection = connection_manager.get_connection_by_user_id(recipient_user_id)
    
    if recipient_connection:
        # Send to local WebSocket
        await connection_manager.send_message(recipient_connection.websocket, message)
        logger.info(f"Received from Redis and sent to {recipient_user_id}: {message.get('text', '')[:50]}...")
        
        # Сохраняем сообщение в историю
        await save_message_to_history(message, recipient_user_id)
    else:
        logger.warning(f"Recipient {recipient_user_id} not found locally (message from {source_container})")
        
        # Сохраняем сообщение в историю (для оффлайн пользователей)
        await save_message_to_history(message, recipient_user_id)


# Include API router
app.include_router(api_router, prefix="/api/v1")

# Serve static files from /app/frontend/dist (after API routes)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    """Serve frontend static files"""
    import os
    from fastapi.responses import FileResponse
    
    dist_path = "/app/frontend/dist"
    file_path = os.path.join(dist_path, full_path)
    
    # If file exists, serve it
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise serve index.html (for SPA routing)
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "File not found"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "chameleon-chat",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_connect(websocket: WebSocket):
    """WebSocket endpoint for real-time messaging"""
    await connection_manager.connect(websocket)
    try:
        await websocket_endpoint(websocket)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(websocket)


async def run_http_server(port: int):
    """Run HTTP server"""
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"HTTP server starting on port {port}")
    await server.serve()


async def run_websocket_server(port: int):
    """Run WebSocket-only server"""
    import uvicorn
    
    # Create a minimal app for WebSocket only
    from fastapi import FastAPI
    ws_app = FastAPI()
    
    @ws_app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await connection_manager.connect(websocket)
        try:
            await websocket_endpoint(websocket)
        except WebSocketDisconnect:
            logger.info("Client disconnected")
            await connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await connection_manager.disconnect(websocket)
    
    config = uvicorn.Config(ws_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"WebSocket server starting on port {port}")
    await server.serve()


async def main():
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting combined server on port {port}")
    logger.info(f"Both HTTP and WebSocket will use port {port}")
    
    # Run single server with both HTTP and WebSocket
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
