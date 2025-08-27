#!/usr/bin/env python3
"""
Authentication Manager for Event Router.

Handles secure token management for GitHub and Claude Code authentication
when spawning agent processes or containers.
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class AuthConfig:
    """Authentication configuration for agents."""

    github_token: Optional[str] = None
    claude_session_path: Optional[Path] = None
    additional_env: Dict[str, str] = None
    mount_home_claude: bool = True  # Mount ~/.claude directory

    def to_env_dict(self) -> Dict[str, str]:
        """Convert to environment variables."""
        env = {}

        if self.github_token:
            # Use GH_TOKEN which is standard for GitHub CLI
            env["GH_TOKEN"] = self.github_token
            env["GITHUB_TOKEN"] = self.github_token

        if self.additional_env:
            env.update(self.additional_env)

        return env


class AuthManager:
    """Manages authentication for agent processes and containers."""

    def __init__(self):
        self.home_dir = Path.home()
        self.claude_dir = self.home_dir / ".claude"
        self.github_token = self._load_github_token()

    def _load_github_token(self) -> Optional[str]:
        """Load GitHub token from environment or config files."""

        # Check environment first
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

        if token:
            logger.info("GitHub token loaded from environment")
            return token

        # Check gh CLI config
        gh_config = self.home_dir / ".config" / "gh" / "hosts.yml"
        if gh_config.exists():
            try:
                import yaml
                with open(gh_config) as f:
                    config = yaml.safe_load(f)
                    # Extract token from gh config
                    if "github.com" in config:
                        token = config["github.com"].get("oauth_token")
                        if token:
                            logger.info("GitHub token loaded from gh CLI config")
                            return token
            except Exception as e:
                logger.warning(f"Failed to load gh config: {e}")

        logger.warning("No GitHub token found")
        return None

    def get_subprocess_env(self, agent_id: str) -> Dict[str, str]:
        """Get environment variables for subprocess execution."""

        env = os.environ.copy()

        # Add GitHub token if available
        if self.github_token:
            env["GH_TOKEN"] = self.github_token
            env["GITHUB_TOKEN"] = self.github_token

        # Add agent ID
        env["AGENT_ID"] = agent_id

        # Claude authentication is handled by copying ~/.claude directory
        # The subprocess will have access to the same auth as parent

        logger.info(f"Prepared environment for subprocess {agent_id}")

        return env

    def prepare_container_auth(
        self,
        agent_id: str,
        container_work_dir: Path = Path("/app")
    ) -> Dict[str, any]:  # type: ignore
        """Prepare authentication for container execution."""

        config = {
            "environment": {},
            "volumes": [],
            "commands": []
        }

        # Add GitHub token as environment variable
        if self.github_token:
            config["environment"]["GH_TOKEN"] = self.github_token
            config["environment"]["GITHUB_TOKEN"] = self.github_token

        # Mount Claude directory for authentication
        if self.claude_dir.exists():
            # Create volume mount for .claude directory
            config["volumes"].append({
                "source": str(self.claude_dir),
                "target": "/home/agent/.claude",
                "type": "bind",
                "read_only": True
            })

            # Also mount to root user's home if different
            config["volumes"].append({
                "source": str(self.claude_dir),
                "target": "/root/.claude",
                "type": "bind",
                "read_only": True
            })

            logger.info(f"Mounted .claude directory for container {agent_id}")
        else:
            logger.warning("No .claude directory found for mounting")

        # Add agent ID
        config["environment"]["AGENT_ID"] = agent_id

        # Add commands to set up user environment in container
        config["commands"] = [
            # Create agent user if it doesn't exist
            "useradd -m -s /bin/bash agent || true",

            # Copy .claude to agent's home if mounted
            "if [ -d /root/.claude ]; then cp -r /root/.claude /home/agent/; chown -R agent:agent /home/agent/.claude; fi",

            # Set up git config for agent user
            "su - agent -c 'git config --global user.name \"Gadugi Agent\"'",
            "su - agent -c 'git config --global user.email \"agent@gadugi.ai\"'",
        ]

        return config

    def create_docker_compose_auth(self, services: List[str]) -> Dict[str, any]:  # type: ignore
        """Create docker-compose configuration with authentication."""

        compose_config = {
            "version": "3.8",
            "services": {},
            "volumes": {
                "claude_auth": {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(self.claude_dir)
                    }
                }
            }
        }

        # Common environment for all services
        common_env = {}
        if self.github_token:
            common_env["GH_TOKEN"] = self.github_token
            common_env["GITHUB_TOKEN"] = self.github_token

        # Configure each service
        for service in services:
            compose_config["services"][service] = {
                "environment": common_env.copy(),
                "volumes": [
                    "claude_auth:/home/agent/.claude:ro",
                    "claude_auth:/root/.claude:ro"
                ]
            }

        return compose_config

    def create_kubernetes_secret(self, namespace: str = "gadugi") -> Dict[str, any]:  # type: ignore
        """Create Kubernetes secret configuration for auth."""

        secret_data = {}

        # Add GitHub token
        if self.github_token:
            import base64
            secret_data["github-token"] = base64.b64encode(
                self.github_token.encode()
            ).decode()

        # For Claude auth, we'd need to create a ConfigMap from .claude directory
        # This is more complex and would require creating a tar archive

        k8s_config = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "gadugi-auth",
                "namespace": namespace
            },
            "type": "Opaque",
            "data": secret_data
        }

        # Also create ConfigMap for .claude directory if it exists
        if self.claude_dir.exists():
            # Create tar archive of .claude directory
            import tarfile
            import base64
            from io import BytesIO

            tar_buffer = BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
                tar.add(self.claude_dir, arcname=".claude")

            claude_tar_b64 = base64.b64encode(tar_buffer.getvalue()).decode()

            configmap = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": "claude-auth",
                    "namespace": namespace
                },
                "binaryData": {
                    "claude-auth.tar.gz": claude_tar_b64
                }
            }

            return {
                "secret": k8s_config,
                "configmap": configmap
            }

        return {"secret": k8s_config}

    def validate_auth(self) -> Dict[str, bool]:
        """Validate that authentication is properly configured."""

        validation = {
            "github_token": False,
            "claude_auth": False,
            "gh_cli": False
        }

        # Check GitHub token
        if self.github_token:
            validation["github_token"] = True

        # Check Claude directory
        if self.claude_dir.exists():
            # Check for key files that indicate auth
            session_files = list(self.claude_dir.glob("*session*"))
            token_files = list(self.claude_dir.glob("*token*"))
            config_files = list(self.claude_dir.glob("*config*"))

            if session_files or token_files or config_files:
                validation["claude_auth"] = True

        # Check gh CLI
        gh_path = shutil.which("gh")
        if gh_path:
            # Try to run gh auth status
            import subprocess
            try:
                result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    validation["gh_cli"] = True
            except Exception:
                pass

        return validation

    def setup_agent_workspace(
        self,
        agent_id: str,
        workspace_path: Path
    ) -> bool:
        """Set up authentication in agent's workspace."""

        try:
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Create .env file with safe environment variables
            env_file = workspace_path / ".env"
            with open(env_file, "w") as f:
                if self.github_token:
                    f.write(f"GH_TOKEN={self.github_token}\n")
                    f.write(f"GITHUB_TOKEN={self.github_token}\n")
                f.write(f"AGENT_ID={agent_id}\n")

            # Create symlink to .claude directory if it exists
            if self.claude_dir.exists():
                agent_claude_dir = workspace_path / ".claude"
                if not agent_claude_dir.exists():
                    agent_claude_dir.symlink_to(self.claude_dir)

            logger.info(f"Set up workspace authentication for {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to set up workspace auth: {e}")
            return False


class ContainerAuthBuilder:
    """Builder for container authentication configurations."""

    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.dockerfile_lines = []
        self.compose_config = {}

    def build_dockerfile_auth(self) -> List[str]:
        """Build Dockerfile lines for authentication setup."""

        lines = [
            "# Authentication setup",
            "RUN useradd -m -s /bin/bash agent",
            "",
            "# Create directories for auth",
            "RUN mkdir -p /home/agent/.claude /root/.claude",
            "",
            "# Copy mounted auth at runtime (handled by entrypoint)",
            'COPY --chown=agent:agent entrypoint.sh /entrypoint.sh',
            'RUN chmod +x /entrypoint.sh',
            "",
            "# Switch to agent user",
            "USER agent",
            "WORKDIR /home/agent",
            "",
            'ENTRYPOINT ["/entrypoint.sh"]'
        ]

        return lines

    def build_entrypoint_script(self) -> str:
        """Build entrypoint script for containers."""

<<<<<<< HEAD
        return """#!/bin/bash
=======
        return '''#!/bin/bash
>>>>>>> feature/gadugi-v0.3-regeneration
set -e

# Copy Claude auth if mounted
if [ -d /mnt/claude-auth ]; then
    cp -r /mnt/claude-auth/. /home/agent/.claude/
    chmod -R 700 /home/agent/.claude
fi

# Set up git config
git config --global user.name "Gadugi Agent"
git config --global user.email "agent@gadugi.ai"

# Export GitHub token if provided
if [ -n "$GH_TOKEN" ]; then
    export GITHUB_TOKEN="$GH_TOKEN"
fi

# Execute the actual command
exec "$@"
<<<<<<< HEAD
"""
=======
'''
>>>>>>> feature/gadugi-v0.3-regeneration

    def build_compose_service(
        self,
        service_name: str,
        image: str,
        command: List[str]
    ) -> Dict[str, any]:  # type: ignore
        """Build docker-compose service with auth."""

        auth_config = self.auth_manager.prepare_container_auth(service_name)

        service = {
            "image": image,
            "container_name": f"gadugi-{service_name}",
            "environment": auth_config["environment"],
            "volumes": [],
            "command": command,
            "networks": ["gadugi-network"]
        }

        # Add volume mounts
        for volume in auth_config["volumes"]:
            service["volumes"].append(
                f"{volume['source']}:{volume['target']}:ro"
            )

        return service


# Example usage
if __name__ == "__main__":
    # Initialize auth manager
    auth_mgr = AuthManager()

    # Validate authentication
    validation = auth_mgr.validate_auth()
    print("Authentication validation:")
    for key, valid in validation.items():
        status = "✓" if valid else "✗"
        print(f"  {status} {key}")

    # Get subprocess environment
    env = auth_mgr.get_subprocess_env("test-agent")
    print(f"\nSubprocess environment has {len(env)} variables")

    # Prepare container auth
    container_config = auth_mgr.prepare_container_auth("test-container")
    print(f"\nContainer config has {len(container_config['volumes'])} volumes")
