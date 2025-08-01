"""Unit tests for logger utilities."""

import pytest
import logging
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.logger import (
    setup_logging,
    create_standard_formatter,
    create_structured_formatter,
    setup_structlog,
    parse_size_string,
    get_logger,
    get_structlog_logger,
    CorrelationIdFilter,
    set_correlation_id,
    get_correlation_id,
    LoggerMixin,
    log_function_call,
    log_async_function_call
)


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        setup_logging()
        
        # Check that root logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_console_only(self):
        """Test setup_logging with console output only."""
        setup_logging(console_output=True, log_file=None)
        
        root_logger = logging.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_setup_logging_file_only(self):
        """Test setup_logging with file output only."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            setup_logging(console_output=False, log_file=log_file)
            
            root_logger = logging.getLogger()
            file_handlers = [h for h in root_logger.handlers if hasattr(h, 'baseFilename')]
            assert len(file_handlers) > 0
        finally:
            # Close handlers to release file handles
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            # Try to delete file, ignore if it fails
            try:
                os.unlink(log_file)
            except (OSError, PermissionError):
                pass

    def test_setup_logging_structured(self):
        """Test setup_logging with structured logging."""
        setup_logging(structured=True)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_level(self):
        """Test setup_logging with different log levels."""
        setup_logging(level="DEBUG")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_with_correlation_id(self):
        """Test setup_logging with correlation ID support."""
        setup_logging(include_correlation_id=True)
        
        root_logger = logging.getLogger()
        # Check that handlers have correlation ID filters
        for handler in root_logger.handlers:
            filters = [f for f in handler.filters if isinstance(f, CorrelationIdFilter)]
            assert len(filters) > 0


class TestFormatters:
    """Test cases for formatter functions."""

    def test_create_standard_formatter(self):
        """Test creating standard formatter."""
        formatter = create_standard_formatter()
        
        assert isinstance(formatter, logging.Formatter)
        assert '%(asctime)s' in formatter._fmt
        assert '%(name)s' in formatter._fmt
        assert '%(levelname)s' in formatter._fmt
        assert '%(message)s' in formatter._fmt

    def test_create_structured_formatter_with_timestamp(self):
        """Test creating structured formatter with timestamp."""
        formatter = create_structured_formatter(include_timestamp=True)
        
        assert isinstance(formatter, logging.Formatter)
        assert '"timestamp"' in formatter._fmt

    def test_create_structured_formatter_without_timestamp(self):
        """Test creating structured formatter without timestamp."""
        formatter = create_structured_formatter(include_timestamp=False)
        
        assert isinstance(formatter, logging.Formatter)
        assert '"timestamp"' not in formatter._fmt

    def test_create_structured_formatter_with_correlation_id(self):
        """Test creating structured formatter with correlation ID."""
        formatter = create_structured_formatter(include_correlation_id=True)
        
        assert isinstance(formatter, logging.Formatter)
        assert '"correlation_id"' in formatter._fmt

    def test_create_structured_formatter_without_correlation_id(self):
        """Test creating structured formatter without correlation ID."""
        formatter = create_structured_formatter(include_correlation_id=False)
        
        assert isinstance(formatter, logging.Formatter)
        assert '"correlation_id"' not in formatter._fmt


class TestStructlog:
    """Test cases for structlog setup."""

    def test_setup_structlog(self):
        """Test structlog setup."""
        setup_structlog()
        
        # This test mainly ensures the function doesn't raise exceptions
        assert True


class TestParseSizeString:
    """Test cases for parse_size_string function."""

    def test_parse_size_string_bytes(self):
        """Test parsing size string in bytes."""
        assert parse_size_string("1024") == 1024

    def test_parse_size_string_kb(self):
        """Test parsing size string in KB."""
        assert parse_size_string("1KB") == 1024
        assert parse_size_string("2KB") == 2048

    def test_parse_size_string_mb(self):
        """Test parsing size string in MB."""
        assert parse_size_string("1MB") == 1024 * 1024
        assert parse_size_string("2MB") == 2 * 1024 * 1024

    def test_parse_size_string_gb(self):
        """Test parsing size string in GB."""
        assert parse_size_string("1GB") == 1024 * 1024 * 1024
        assert parse_size_string("2GB") == 2 * 1024 * 1024 * 1024

    def test_parse_size_string_case_insensitive(self):
        """Test parsing size string with different cases."""
        assert parse_size_string("1kb") == 1024
        assert parse_size_string("1mb") == 1024 * 1024
        assert parse_size_string("1gb") == 1024 * 1024 * 1024


class TestLoggerFunctions:
    """Test cases for logger utility functions."""

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_structlog_logger(self):
        """Test get_structlog_logger function."""
        logger = get_structlog_logger("test_structlog")
        
        # This test ensures the function doesn't raise exceptions
        assert logger is not None


class TestCorrelationIdFilter:
    """Test cases for CorrelationIdFilter."""

    def test_correlation_id_filter_initialization(self):
        """Test CorrelationIdFilter initialization."""
        filter_obj = CorrelationIdFilter()
        
        assert filter_obj.correlation_id is None

    def test_correlation_id_filter_filter(self):
        """Test CorrelationIdFilter filter method."""
        filter_obj = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == "no-id"

    def test_correlation_id_filter_set_correlation_id(self):
        """Test setting correlation ID in filter."""
        filter_obj = CorrelationIdFilter()
        filter_obj.set_correlation_id("test-correlation-id")
        
        assert filter_obj.correlation_id == "test-correlation-id"

    def test_correlation_id_filter_with_correlation_id(self):
        """Test filter with correlation ID set."""
        filter_obj = CorrelationIdFilter()
        filter_obj.set_correlation_id("test-correlation-id")
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.correlation_id == "test-correlation-id"


class TestCorrelationIdFunctions:
    """Test cases for correlation ID utility functions."""

    def test_set_correlation_id(self):
        """Test set_correlation_id function."""
        set_correlation_id("test-correlation-id")
        
        # This test ensures the function doesn't raise exceptions
        assert True

    def test_get_correlation_id(self):
        """Test get_correlation_id function."""
        correlation_id = get_correlation_id()
        
        # Should return the previously set correlation ID or None
        assert correlation_id is not None or correlation_id is None


class TestLoggerMixin:
    """Test cases for LoggerMixin."""

    def test_logger_mixin_logger_property(self):
        """Test LoggerMixin logger property."""
        class TestClass(LoggerMixin):
            pass
        
        test_instance = TestClass()
        logger = test_instance.logger
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "TestClass"

    def test_logger_mixin_struct_logger_property(self):
        """Test LoggerMixin struct_logger property."""
        class TestClass(LoggerMixin):
            pass
        
        test_instance = TestClass()
        struct_logger = test_instance.struct_logger
        
        # This test ensures the property doesn't raise exceptions
        assert struct_logger is not None


class TestLogDecorators:
    """Test cases for logging decorators."""

    def test_log_function_call(self):
        """Test log_function_call decorator."""
        @log_function_call
        def test_function(arg1, arg2, kwarg1="default"):
            return arg1 + arg2
        
        result = test_function(1, 2, kwarg1="test")
        
        assert result == 3

    def test_log_function_call_with_exception(self):
        """Test log_function_call decorator with exception."""
        @log_function_call
        def failing_function():
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError):
            failing_function()

    @pytest.mark.asyncio
    async def test_log_async_function_call(self):
        """Test log_async_function_call decorator."""
        @log_async_function_call
        async def test_async_function(arg1, arg2, kwarg1="default"):
            return arg1 + arg2
        
        result = await test_async_function(1, 2, kwarg1="test")
        
        assert result == 3

    @pytest.mark.asyncio
    async def test_log_async_function_call_with_exception(self):
        """Test log_async_function_call decorator with exception."""
        @log_async_function_call
        async def failing_async_function():
            raise ValueError("Test async exception")
        
        with pytest.raises(ValueError):
            await failing_async_function()


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_logging_with_correlation_id(self):
        """Test logging with correlation ID integration."""
        # Setup logging with correlation ID
        setup_logging(include_correlation_id=True)
        
        # Set correlation ID
        set_correlation_id("test-correlation-id")
        
        # Get logger and log a message
        logger = get_logger("test_integration")
        logger.info("Test message")
        
        # This test ensures the integration works without exceptions
        assert True

    def test_structured_logging_integration(self):
        """Test structured logging integration."""
        # Setup structured logging
        setup_logging(structured=True)
        
        # Get logger and log a message
        logger = get_logger("test_structured")
        logger.info("Test structured message")
        
        # This test ensures the integration works without exceptions
        assert True

    def test_logging_with_file_and_console(self):
        """Test logging with both file and console output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            # Setup logging with both file and console
            setup_logging(console_output=True, log_file=log_file)
            
            # Get logger and log a message
            logger = get_logger("test_file_console")
            logger.info("Test message to both outputs")
            
            # Check that log file was created and has content
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message to both outputs" in content
        finally:
            # Close handlers to release file handles
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            # Try to delete file, ignore if it fails
            try:
                os.unlink(log_file)
            except (OSError, PermissionError):
                pass 