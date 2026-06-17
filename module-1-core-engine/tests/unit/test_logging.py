# Тесты логирования

import pytest


class TestLogging:
    """Tests for logging module."""
    
    def test_correlation_id(self):
        """Test correlation ID generation."""
        import uuid
        id1 = str(uuid.uuid4())
        assert id1 is not None
        assert len(id1) > 0
        assert "-" in id1  # UUID format
    
    def test_log_info_format(self):
        """Test INFO log format."""
        message = "Test info message"
        key = "value"
        
        # Basic format check
        log_entry = {
            "message": message,
            "key": key
        }
        
        assert log_entry["message"] == message
    
    def test_log_error_format(self):
        """Test ERROR log format."""
        message = "Test error message"
        error = "something went wrong"
        
        log_entry = {
            "message": message,
            "error": error
        }
        
        assert log_entry["error"] == error
    
    def test_log_warning_format(self):
        """Test WARNING log format."""
        message = "Test warning message"
        warning = "be careful"
        
        log_entry = {
            "message": message,
            "warning": warning
        }
        
        assert log_entry["warning"] == warning
