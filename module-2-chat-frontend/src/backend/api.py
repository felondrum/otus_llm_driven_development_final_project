# ===========================================
# REST API endpoints for Chat Frontend
# ===========================================

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Хранилище сообщений в памяти (для демонстрации)
# В реальном приложении нужно использовать базу данных
# Все сообщения хранятся в одном списке и фильтруются по需要
all_chat_messages = []


# Import from websocket module (same directory)
from websocket import TEST_USERS, STYLES, connection_manager

# These are now just data, not async functions


@api_router.get("/users")
async def list_users():
    """Get list of test users"""
    return {"users": TEST_USERS}


@api_router.get("/styles")
async def list_styles():
    """Get list of available styles"""
    return {"styles": STYLES}


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chameleon-chat-api"}


@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "chameleon-chat-api",
        "version": "1.0.0",
        "endpoints": {
            "users": "/api/v1/users",
            "styles": "/api/v1/styles",
            "health": "/api/v1/health",
            "messages": "/api/v1/messages/{recipient_id}"
        }
    }


@api_router.get("/messages/{recipient_id}")
async def get_chat_history(recipient_id: str):
    """Get chat history with a specific recipient"""
    # Фильтруем все сообщения, чтобы показать только те, где участвует текущий пользователь
    # (отправленные нами или полученные нами)
    filtered_messages = [
        msg for msg in all_chat_messages 
        if msg.get("from") == recipient_id or msg.get("to") == recipient_id
    ]
    return {"messages": filtered_messages}


@api_router.post("/messages/{recipient_id}")
async def save_message(recipient_id: str, message: dict):
    """Save a message to chat history"""
    # Используем recipient_id как получателя, извлекаем отправителя из сообщения
    sender_id = message.get("from")
    
    if not sender_id:
        return {"status": "error", "message": "Message must have 'from' field"}
    
    # Просто добавляем сообщение в общий список
    all_chat_messages.append(message)
    return {"status": "saved", "message_id": message.get("id")}
