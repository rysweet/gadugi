#!/usr/bin/env python3
"""
Tests for Integration Test Agent Agent Engine
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'orchestrator'))

from integration_test_agent_engine import IntegrationTestAgentEngine, IntegrationTestAgentRequest, IntegrationTestAgentResponse


class TestIntegrationTestAgentEngine(unittest.TestCase):
    """Test cases for IntegrationTestAgent Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = IntegrationTestAgentEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes properly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)
    
    def test_basic_operation(self):
        """Test basic operation execution."""
        request = IntegrationTestAgentRequest(
            operation="test",
            parameters={"test_param": "test_value"},
            options={}
        )
        
        response = self.engine.execute_operation(request)
        
        self.assertIsInstance(response, IntegrationTestAgentResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.operation, "test")
        self.assertEqual(len(response.errors), 0)
    
    def test_invalid_operation(self):
        """Test handling of invalid operations.""" 
        request = IntegrationTestAgentRequest(
            operation="invalid_operation",
            parameters={},
            options={}
        )
        
        response = self.engine.execute_operation(request)
        
        self.assertIsInstance(response, IntegrationTestAgentResponse)
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
        self.assertEqual(self.engine.logger.name, "integration_test_agent")
    
    def test_request_response_dataclasses(self):
        """Test request and response dataclass functionality."""
        request = IntegrationTestAgentRequest(
            operation="test",
            parameters={"key": "value"},
            options={"option": True}
        )
        
        self.assertEqual(request.operation, "test")
        self.assertEqual(request.parameters["key"], "value") 
        self.assertTrue(request.options["option"])
        
        response = IntegrationTestAgentResponse(
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
