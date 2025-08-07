#!/usr/bin/env python3
"""Setup script for Gadugi v0.3 - Clean implementation of multi-agent framework."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = "Gadugi v0.3 - Multi-agent development framework"

setup(
    name="gadugi-v3",
    version="0.3.0",
    author="Gadugi Team",
    description="Clean implementation of Gadugi multi-agent framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rysweet/gadugi",
    
    # Find all Python packages
    packages=find_packages(where=".", include=["src*", "services*", "tests*"]),
    
    # Map packages to their directories
    package_dir={
        "": ".",
        "gadugi": "src",
        "gadugi.orchestrator": "src/orchestrator",
        "gadugi.services": "services",
        "gadugi.services.cli": "services/cli",
        "gadugi.services.event_router": "services/event-router",
        "gadugi.services.llm_proxy": "services/llm-proxy",
        "gadugi.services.mcp": "services/mcp",
        "gadugi.services.neo4j": "services/neo4j-graph",
    },
    
    # Include all data files
    package_data={
        "gadugi": [
            # Agent markdown files
            "../agents/**/*.md",
            "../agents/**/README.md",
            "../agents/**/workflows/*.md",
            "../agents/**/knowledge/*.md",
            "../agents/**/memories/*.md",
            "../agents/**/templates/*.md",
            
            # Service configurations
            "../services/**/*.json",
            "../services/**/*.yaml",
            "../services/**/*.yml",
            "../services/**/*.proto",
            
            # Test data
            "../tests/**/*.json",
            "../tests/**/*.yaml",
            "../tests/**/*.md",
            
            # Configuration files
            "../pyproject.toml",
            "../.gadugi/**/*.json",
            "../.gadugi/**/*.yaml",
        ],
    },
    
    # Include everything in MANIFEST.in
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.9",
    
    # Dependencies
    install_requires=[
        # Core dependencies - add as needed
        "pyyaml>=6.0",
        "aiofiles>=23.0",
        "asyncio>=3.4",
    ],
    
    # Optional dependencies for different features
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
        ],
        "services": [
            "neo4j>=5.0",
            "redis>=4.0",
            "protobuf>=4.0",
            "aiohttp>=3.8",
        ],
        "llm": [
            "openai>=1.0",
            "anthropic>=0.5",
        ],
    },
    
    # Console scripts
    entry_points={
        "console_scripts": [
            "gadugi-v3=gadugi.cli:main",
            "gadugi-orchestrator=gadugi.orchestrator.run_agent:main",
            "gadugi-cli=gadugi.services.cli.gadugi_cli_service:main",
            "gadugi-event-router=gadugi.services.event_router.event_router_service:main",
            "gadugi-mcp=gadugi.services.mcp.mcp_service:main",
            "gadugi-llm-proxy=gadugi.services.llm_proxy.llm_proxy_service:main",
            "gadugi-neo4j=gadugi.services.neo4j.neo4j_graph_service:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)