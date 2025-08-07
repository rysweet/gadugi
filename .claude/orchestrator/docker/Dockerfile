# Claude Orchestrator Docker Image
# Provides containerized execution environment for parallel WorkflowManager tasks
FROM python:3.11-slim

LABEL maintainer="Gadugi Orchestrator"
LABEL description="Containerized execution environment for Claude Code orchestrator"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    procps \
    htop \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI (simulated - replace with actual installation)
# NOTE: Replace this with the actual Claude CLI installation method
RUN echo '#!/bin/bash' > /usr/local/bin/claude && \
    echo 'echo "Claude CLI placeholder - replace with actual Claude CLI"' >> /usr/local/bin/claude && \
    echo 'echo "Command: $@"' >> /usr/local/bin/claude && \
    echo 'echo "Working directory: $(pwd)"' >> /usr/local/bin/claude && \
    echo 'echo "Files in workspace:"' >> /usr/local/bin/claude && \
    echo 'ls -la' >> /usr/local/bin/claude && \
    chmod +x /usr/local/bin/claude

# Install Python dependencies for container execution
RUN pip install --no-cache-dir \
    docker \
    psutil \
    websockets \
    asyncio \
    aiofiles \
    pydantic \
    requests \
    gitpython

# Create working directory
WORKDIR /workspace

# Create results directory for output collection
RUN mkdir -p /workspace/results

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace
ENV CLAUDE_CONTAINER_MODE=1

# Health check to ensure container is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command runs bash for interactive debugging
CMD ["bash"]