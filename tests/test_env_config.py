#!/usr/bin/env python3
"""Test environment variable configuration for Neo4j and other services."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Neo4j module correctly
neo4j_path = Path(__file__).parent.parent / 'neo4j'
sys.path.insert(0, str(neo4j_path))

from neo4j_client import Neo4jConfig


class TestEnvironmentVariableConfiguration(unittest.TestCase):
    """Test that environment variables are properly used for configuration."""

    def test_neo4j_config_uses_env_vars(self):
        """Test that Neo4jConfig reads from environment variables."""
        # Set test environment variables
        test_env = {
            'NEO4J_HOST': 'test-host',
            'NEO4J_BOLT_PORT': '9999',
            'NEO4J_USERNAME': 'test-user',
            'NEO4J_PASSWORD': 'test-password',
            'NEO4J_DATABASE': 'test-db'
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            config = Neo4jConfig()
            
            # Verify configuration uses environment variables
            self.assertEqual(config.uri, 'bolt://test-host:9999')
            self.assertEqual(config.username, 'test-user')
            self.assertEqual(config.password, 'test-password')
            self.assertEqual(config.database, 'test-db')
    
    def test_neo4j_config_fallback_values(self):
        """Test that Neo4jConfig uses fallback values when env vars not set."""
        # Clear relevant environment variables
        env_vars_to_clear = ['NEO4J_HOST', 'NEO4J_BOLT_PORT', 'NEO4J_USERNAME', 
                              'NEO4J_PASSWORD', 'NEO4J_DATABASE']
        
        # Create a copy of environ without our variables
        clean_env = {k: v for k, v in os.environ.items() 
                     if k not in env_vars_to_clear}
        
        with patch.dict(os.environ, clean_env, clear=True):
            config = Neo4jConfig()
            
            # Verify fallback values are used
            self.assertEqual(config.uri, 'bolt://localhost:7687')
            self.assertEqual(config.username, 'neo4j')
            self.assertEqual(config.password, 'changeme')
            self.assertEqual(config.database, 'gadugi')
    
    def test_no_hardcoded_secrets_in_code(self):
        """Verify no hardcoded secrets remain in the configuration."""
        config = Neo4jConfig()
        
        # These hardcoded values should no longer exist
        forbidden_passwords = ['gadugi123', 'gadugi-password']
        
        # Check that none of the forbidden passwords are in use
        self.assertNotIn(config.password, forbidden_passwords,
                        f"Found hardcoded password: {config.password}")
    
    def test_env_example_file_exists(self):
        """Verify that .env.example file exists with proper template."""
        env_example_path = Path(__file__).parent.parent / '.env.example'
        
        self.assertTrue(env_example_path.exists(), 
                       ".env.example file does not exist")
        
        # Read and verify content
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Check for required environment variables
        required_vars = [
            'NEO4J_PASSWORD',
            'NEO4J_AUTH',
            'NEO4J_HOST',
            'NEO4J_BOLT_PORT',
            'NEO4J_DATABASE'
        ]
        
        for var in required_vars:
            self.assertIn(var, content, 
                         f"Missing {var} in .env.example")
    
    def test_docker_compose_uses_env_vars(self):
        """Verify docker-compose files use environment variables."""
        docker_compose_path = Path(__file__).parent.parent / 'docker-compose.yml'
        
        if docker_compose_path.exists():
            with open(docker_compose_path, 'r') as f:
                content = f.read()
            
            # Check for environment variable syntax
            self.assertIn('${NEO4J_AUTH', content,
                         "docker-compose.yml should use NEO4J_AUTH env var")
            
            # Verify no hardcoded passwords
            self.assertNotIn('gadugi123', content,
                           "Found hardcoded password in docker-compose.yml")
    
    def test_gitignore_includes_env_file(self):
        """Verify that .env file is in .gitignore."""
        gitignore_path = Path(__file__).parent.parent / '.gitignore'
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            # Check that .env is ignored
            self.assertIn('.env', content,
                         ".env file must be in .gitignore for security")


if __name__ == '__main__':
    unittest.main()