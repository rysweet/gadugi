#!/usr/bin/env python3
"""
Tests for Api Client Agent Engine
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'orchestrator'))

from api_client_engine import ApiClientEngine, ApiClientRequest, ApiClientResponse


class TestApiClientEngine(unittest.TestCase):
    """Test cases for ApiClient Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = ApiClientEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes properly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)
    
    def test_basic_operation(self):
        """Test basic operation execution."""
        request = ApiClientRequest(
            operation="test",
            parameters={"test_param": "test_value"},
            options={}
        )
        
        response = self.engine.execute_operation(request)
        
        self.assertIsInstance(response, ApiClientResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.operation, "test")
        self.assertEqual(len(response.errors), 0)
    
    def test_invalid_operation(self):
        """Test handling of invalid operations.""" 
        request = ApiClientRequest(
            operation="invalid_operation",
            parameters={},
            options={}
        )
        
        response = self.engine.execute_operation(request)
        
        self.assertIsInstance(response, ApiClientResponse)
        # Should still succeed with default handling
        self.assertTrue(response.success)
    
    def test_error_handling(self):
        """Test error handling in operations."""
        # This test would need specific error conditions
        # based on the agent's implementation
        pass
    
    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.engine.logger)
        self.assertEqual(self.engine.logger.name, "api_client")
    
    def test_request_response_dataclasses(self):
        """Test request and response dataclass functionality."""
        request = ApiClientRequest(
            operation="test",
            parameters={"key": "value"},
            options={"option": True}
        )
        
        self.assertEqual(request.operation, "test")
        self.assertEqual(request.parameters["key"], "value") 
        self.assertTrue(request.options["option"])
        
        response = ApiClientResponse(
            success=True,
            operation="test",
            results={"result": "success"},
            warnings=[],
            errors=[]
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.operation, "test")
        self.assertEqual(response.results["result"], "success")


if __name__ == '__main__':
    unittest.main()
