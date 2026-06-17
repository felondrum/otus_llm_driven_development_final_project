# Тесты обработчиков сообщений для оркестратора

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_config():
    """Mock config fixture."""
    config = MagicMock()
    config.redis_host = "localhost"
    config.redis_port = 6379
    config.cache_ttl = 300
    return config


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager fixture."""
    cache_manager = MagicMock()
    cache_manager.generate_key = MagicMock(return_value="test_cache_key")
    cache_manager.get = MagicMock(return_value=None)
    cache_manager.set = MagicMock(return_value=None)
    return cache_manager


@pytest.fixture
def mock_context_assembler():
    """Mock context assembler fixture."""
    context_assembler = MagicMock()
    context_assembler.assemble_context = MagicMock(return_value="Test prompt")
    return context_assembler


@pytest.fixture
def mock_cache_manager_empty():
    """Mock cache manager with empty cache."""
    cache_manager = MagicMock()
    cache_manager.generate_key = MagicMock(return_value="test_key")
    cache_manager.get = MagicMock(return_value=None)
    cache_manager.set = MagicMock(return_value=None)
    return cache_manager


@pytest.fixture
def mock_context_assembler_empty():
    """Mock context assembler with empty context."""
    context_assembler = MagicMock()
    context_assembler.assemble_context = MagicMock(return_value="")
    return context_assembler


class TestMessageHandler:
    """Tests for MessageHandler with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_process_message_cache_miss(self, mock_config, mock_cache_manager, mock_context_assembler):
        """Test message processing with cache miss."""
        from orchestrator.handlers import MessageHandler
        
        # Mock get_cache_manager and get_context_assembler during __init__
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler):
            
            handler = MessageHandler(config=mock_config)
            
            result = await handler.process_message(
                message_id="msg-001",
                sender_id="user-1",
                recipient_id="user-2",
                text="Hello",
                room_id="room-1",
                style_name="formal"
            )
            
            # Verify cache was checked
            mock_cache_manager.generate_key.assert_called_once()
            mock_cache_manager.get.assert_called_once()
            
            # Verify context was assembled
            mock_context_assembler.assemble_context.assert_called_once()
            
            # Verify response structure
            assert result['adapted_text'] == "Adapted: Hello"
            assert result['was_adapted'] == True
            assert result['from_cache'] == False
            assert result['message_id'] == "msg-001"
    
    @pytest.mark.asyncio
    async def test_process_message_cache_hit(self, mock_config, mock_cache_manager, mock_context_assembler):
        """Test message processing with cache hit."""
        from orchestrator.handlers import MessageHandler
        
        # Set up cached response
        cached_response = {
            'adapted_text': 'Cached adapted text',
            'was_adapted': True,
            'confidence': 0.98,
            'model_used': 'llama3.2:3b',
            'processing_time_ms': 50,
            'rules_applied': ['rule-1'],
            'from_cache': True
        }
        mock_cache_manager.get = MagicMock(return_value=cached_response)
        
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler):
            
            handler = MessageHandler(config=mock_config)
            
            result = await handler.process_message(
                message_id="msg-002",
                sender_id="user-1",
                recipient_id="user-2",
                text="Hello"
            )
            
            # Verify cache was hit
            mock_cache_manager.get.assert_called_once()
            
            # Verify cached response returned
            assert result['adapted_text'] == 'Cached adapted text'
            assert result['from_cache'] == True
            assert result['confidence'] == 0.98
            
            # Context assembler should NOT be called on cache hit
            mock_context_assembler.assemble_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_batch_process_messages(self, mock_config, mock_cache_manager, mock_context_assembler):
        """Test batch message processing."""
        from orchestrator.handlers import MessageHandler
        
        # Mock get_cache_manager and get_context_assembler during __init__
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler):
            
            handler = MessageHandler(config=mock_config)
            
            # Mock process_message for batch processing
            async def mock_process_message(*args, **kwargs):
                return {
                    'adapted_text': f"Adapted: {kwargs.get('text', '')}",
                    'was_adapted': True,
                    'from_cache': False,
                    'message_id': kwargs.get('message_id', ''),
                    'room_id': kwargs.get('room_id'),
                    'style_name': kwargs.get('style_name')
                }
            
            handler.process_message = mock_process_message
            
            messages = [
                {
                    'message_id': 'msg-1',
                    'sender_id': 'user-1',
                    'recipient_id': 'user-2',
                    'text': 'First message'
                },
                {
                    'message_id': 'msg-2',
                    'sender_id': 'user-2',
                    'recipient_id': 'user-1',
                    'text': 'Second message',
                    'room_id': 'room-1',
                    'style_name': 'casual'
                }
            ]
            
            results = await handler.batch_process_messages(messages)
            
            # Verify correct number of results
            assert len(results) == 2
            
            # Verify first result
            assert results[0]['message_id'] == 'msg-1'
            assert results[0]['adapted_text'] == 'Adapted: First message'
            
            # Verify second result
            assert results[1]['message_id'] == 'msg-2'
            assert results[1]['room_id'] == 'room-1'
            assert results[1]['style_name'] == 'casual'


class TestMessageHandlerEdgeCases:
    """Tests for edge cases in MessageHandler."""
    
    @pytest.mark.asyncio
    async def test_process_message_empty_text(self, mock_config, mock_cache_manager_empty, mock_context_assembler_empty):
        """Test message processing with empty text."""
        from orchestrator.handlers import MessageHandler
        
        # Mock get_cache_manager and get_context_assembler during __init__
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager_empty), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler_empty):
            
            handler = MessageHandler(config=mock_config)
            
            result = await handler.process_message(
                message_id="msg-003",
                sender_id="user-1",
                recipient_id="user-2",
                text=""
            )
            
            # Should still return valid response
            assert 'adapted_text' in result
            assert 'message_id' in result
    
    @pytest.mark.asyncio
    async def test_batch_process_empty_list(self, mock_config, mock_cache_manager_empty, mock_context_assembler_empty):
        """Test batch processing with empty list."""
        from orchestrator.handlers import MessageHandler
        
        # Mock get_cache_manager and get_context_assembler during __init__
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager_empty), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler_empty):
            
            handler = MessageHandler(config=mock_config)
            
            results = await handler.batch_process_messages([])
            
            # Should return empty list
            assert results == []
    
    @pytest.mark.asyncio
    async def test_process_message_without_optional_params(self, mock_config, mock_cache_manager_empty, mock_context_assembler_empty):
        """Test message processing without optional parameters."""
        from orchestrator.handlers import MessageHandler
        
        # Mock get_cache_manager and get_context_assembler during __init__
        with patch('orchestrator.handlers.get_cache_manager', return_value=mock_cache_manager_empty), \
             patch('orchestrator.handlers.get_context_assembler', return_value=mock_context_assembler_empty):
            
            handler = MessageHandler(config=mock_config)
            
            result = await handler.process_message(
                message_id="msg-004",
                sender_id="user-1",
                recipient_id="user-2",
                text="Test"
                # room_id and style_name are optional
            )
            
            # Should work without optional params
            assert result['message_id'] == "msg-004"
            assert result['room_id'] is None
            assert 'style_name' not in result or result.get('style_name') is None


class TestMessageHandlerSingleton:
    """Tests for MessageHandler singleton pattern."""
    
    def test_get_message_handler_singleton(self, mock_config):
        """Test that get_message_handler returns singleton."""
        from orchestrator.handlers import get_message_handler, _handler
        
        # Reset global handler
        from orchestrator.handlers import _handler as global_handler_var
        global global_handler_var
        global_handler_var = None
        
        # Mock get_cache_manager to avoid Redis connection
        with patch('orchestrator.handlers.get_cache_manager') as mock_get_cache:
            mock_cache = MagicMock()
            mock_get_cache.return_value = mock_cache
            
            handler1 = get_message_handler(config=mock_config)
            handler2 = get_message_handler(config=mock_config)
        
        # Both should reference the same instance
        assert handler1 is handler2
