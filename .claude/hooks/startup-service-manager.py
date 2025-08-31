#!/usr/bin/env python3
"""
Enhanced Service Management Agent for Gadugi v0.3
Checks .env configuration, verifies services, and auto-configures/restarts as needed.
Integrates with Claude Code SessionStart hook.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any


# ANSI color codes for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color
    BOLD = "\033[1m"


class ServiceManager:
    """Enhanced service manager with configuration checking and auto-repair."""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.gadugi_root = self.script_dir.parent.parent
        self.gadugi_dir = self.gadugi_root / ".gadugi"
        self.env_file = self.gadugi_dir / ".env"
        self.env_example = self.gadugi_dir / ".env.example"
        self.services_config = self.load_services_config()
        self.issues_found = []
        self.actions_taken = []

    def load_services_config(self) -> Dict[str, Any]:
        """Load service configuration."""
        return {
            "neo4j": {
                "name": "Neo4j Database",
                "required": True,
                "check_command": [
                    "docker",
                    "ps",
                    "--filter",
                    "name=gadugi-neo4j",
                    "--format",
                    "{{.Status}}",
                ],
                "ports": {"bolt": 7689, "http": 7475},
                "env_vars": {
                    "NEO4J_URI": "bolt://localhost:7689",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "gadugi-password",
                    "NEO4J_DATABASE": "neo4j",
                    "NEO4J_HOST": "localhost",
                    "NEO4J_BOLT_PORT": "7689",
                    "NEO4J_HTTP_PORT": "7475",
                },
            },
            "mcp": {
                "name": "MCP Service (Memory API)",
                "required": True,
                "check_url": "http://localhost:8000/health",
                "start_script": ".gadugi/src/src/services/mcp/start_neo4j_mcp.py",
                "env_vars": {
                    "MCP_NEO4J_URI": "bolt://localhost:7689",
                    "MCP_NEO4J_PASSWORD": "gadugi-password",
                },
            },
            "event-router": {
                "name": "Event Router",
                "required": False,
                "check_url": "http://localhost:8001/health",
                "start_script": ".gadugi/src/src/services/event-router/start_event_router.py",
                "env_vars": {},
            },
        }

    def print_header(self):
        """Print a formatted header."""
        print(f"\n{Colors.BLUE}{'='*80}{Colors.NC}")
        print(
            f"{Colors.CYAN}{Colors.BOLD}🔧 Gadugi v0.3 Enhanced Service Manager{Colors.NC}"
        )
        print(f"{Colors.BLUE}{'='*80}{Colors.NC}\n")

    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{Colors.PURPLE}### {title}{Colors.NC}")
        print(f"{Colors.PURPLE}{'-'*40}{Colors.NC}")

    def print_status(self, status: str, message: str):
        """Print a status message with appropriate color."""
        if status == "success":
            print(f"{Colors.GREEN}✅ {message}{Colors.NC}")
        elif status == "warning":
            print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")
        elif status == "error":
            print(f"{Colors.RED}❌ {message}{Colors.NC}")
        elif status == "info":
            print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")
        elif status == "action":
            print(f"{Colors.CYAN}🚀 {message}{Colors.NC}")

    def check_env_file(self) -> bool:
        """Check if .env file exists and create if needed."""
        self.print_section("Environment Configuration Check")

        if not self.env_file.exists():
            self.print_status("warning", f".env file not found at {self.env_file}")
            self.issues_found.append("Missing .env file")

            if self.env_example.exists():
                self.print_status("info", f"Found .env.example at {self.env_example}")
                return self.create_env_file()
            else:
                self.print_status(
                    "error", ".env.example not found - cannot auto-create configuration"
                )
                return False
        else:
            self.print_status("success", f".env file exists at {self.env_file}")
            return self.validate_env_file()

    def create_env_file(self) -> bool:
        """Create .env file from example with correct Neo4j settings."""
        self.print_status(
            "action", "Creating .env file with proper Neo4j configuration..."
        )

        env_content = """# Gadugi Environment Variables
# Auto-generated by Service Manager

# Neo4j Configuration
NEO4J_AUTH=neo4j/gadugi-password
NEO4J_PASSWORD=gadugi-password

# Connection settings - using non-default ports to avoid conflicts
NEO4J_HOST=localhost
NEO4J_BOLT_PORT=7689  # Non-default Bolt port
NEO4J_HTTP_PORT=7475  # Non-default HTTP port
NEO4J_DATABASE=neo4j  # Using default database

# Memory and performance tuning for Neo4j
NEO4J_PAGECACHE_SIZE=1G
NEO4J_HEAP_INITIAL_SIZE=1G
NEO4J_HEAP_MAX_SIZE=2G

# Docker Compose Environment
COMPOSE_PROJECT_NAME=gadugi

# MCP Service Configuration
NEO4J_URI=bolt://localhost:7689
NEO4J_USERNAME=neo4j
MCP_NEO4J_URI=bolt://localhost:7689
MCP_NEO4J_PASSWORD=gadugi-password

# Event Router Configuration
EVENT_ROUTER_PORT=8001
MEMORY_BACKEND_URL=http://localhost:8000
"""

        try:
            self.env_file.write_text(env_content)
            self.print_status("success", f"Created .env file at {self.env_file}")
            self.actions_taken.append("Created .env configuration file")
            return True
        except Exception as e:
            self.print_status("error", f"Failed to create .env file: {e}")
            return False

    def validate_env_file(self) -> bool:
        """Validate that .env file has correct Neo4j configuration."""
        self.print_status("info", "Validating .env configuration...")

        try:
            env_vars = {}
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()

            # Check critical Neo4j settings
            required_vars = {
                "NEO4J_BOLT_PORT": "7689",
                "NEO4J_PASSWORD": "gadugi-password",
                "NEO4J_DATABASE": "neo4j",
                "NEO4J_URI": "bolt://localhost:7689",
            }

            missing_or_wrong = []
            for var, expected in required_vars.items():
                if var not in env_vars:
                    missing_or_wrong.append(f"{var} (missing)")
                elif env_vars[var] != expected:
                    missing_or_wrong.append(
                        f"{var} (expected: {expected}, got: {env_vars[var]})"
                    )

            if missing_or_wrong:
                self.print_status("warning", "Found configuration issues:")
                for issue in missing_or_wrong:
                    print(f"  - {issue}")
                self.issues_found.append("Incorrect .env configuration")

                # Offer to fix
                return self.fix_env_configuration(env_vars, required_vars)
            else:
                self.print_status(
                    "success",
                    "All critical environment variables are correctly configured",
                )
                return True

        except Exception as e:
            self.print_status("error", f"Failed to validate .env file: {e}")
            return False

    def fix_env_configuration(self, current_vars: Dict, required_vars: Dict) -> bool:
        """Fix incorrect environment variables."""
        self.print_status("action", "Fixing environment configuration...")

        # Update current vars with required values
        current_vars.update(required_vars)

        # Rebuild .env file
        lines = []
        lines.append("# Gadugi Environment Variables")
        lines.append("# Auto-fixed by Service Manager")
        lines.append("")

        # Group variables
        neo4j_vars = {k: v for k, v in current_vars.items() if k.startswith("NEO4J")}
        other_vars = {
            k: v for k, v in current_vars.items() if not k.startswith("NEO4J")
        }

        lines.append("# Neo4j Configuration")
        for key, value in sorted(neo4j_vars.items()):
            lines.append(f"{key}={value}")

        if other_vars:
            lines.append("")
            lines.append("# Other Configuration")
            for key, value in sorted(other_vars.items()):
                lines.append(f"{key}={value}")

        try:
            self.env_file.write_text("\n".join(lines) + "\n")
            self.print_status("success", "Fixed environment configuration")
            self.actions_taken.append("Fixed .env configuration")
            return True
        except Exception as e:
            self.print_status("error", f"Failed to fix .env file: {e}")
            return False

    def check_neo4j(self) -> bool:
        """Check if Neo4j is running and accessible."""
        self.print_section("Neo4j Database Check")

        # Check if Neo4j container is running
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=gadugi-neo4j",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "Up" in result.stdout:
                self.print_status("success", "Neo4j container is running")

                # Test connection
                return self.test_neo4j_connection()
            else:
                self.print_status("error", "Neo4j container is not running")
                self.issues_found.append("Neo4j not running")
                return self.start_neo4j()

        except subprocess.TimeoutExpired:
            self.print_status("error", "Timeout checking Neo4j status")
            return False
        except FileNotFoundError:
            self.print_status("error", "Docker not found - cannot check Neo4j")
            return False

    def test_neo4j_connection(self) -> bool:
        """Test Neo4j connection using the configured port."""
        self.print_status("info", "Testing Neo4j connection on port 7689...")

        test_script = """
import sys
from neo4j import GraphDatabase
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7689")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "gadugi-password")

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        if result.single()["test"] == 1:
            print("SUCCESS")
            sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    if 'driver' in locals():
        driver.close()
"""

        try:
            # Set environment variables
            env = os.environ.copy()
            env.update(
                {
                    "NEO4J_URI": "bolt://localhost:7689",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "gadugi-password",
                }
            )

            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )

            if result.returncode == 0 and "SUCCESS" in result.stdout:
                self.print_status("success", "Neo4j connection successful")
                return True
            else:
                self.print_status(
                    "error", f"Neo4j connection failed: {result.stdout}{result.stderr}"
                )
                self.issues_found.append("Neo4j connection failed")
                return False

        except subprocess.TimeoutExpired:
            self.print_status("error", "Timeout connecting to Neo4j")
            return False
        except Exception as e:
            self.print_status("error", f"Error testing Neo4j: {e}")
            return False

    def start_neo4j(self) -> bool:
        """Start Neo4j container."""
        self.print_status("action", "Starting Neo4j container...")

        docker_compose_file = self.gadugi_root / "docker-compose.yml"
        if not docker_compose_file.exists():
            docker_compose_file = self.gadugi_dir / "docker-compose.yml"

        if not docker_compose_file.exists():
            self.print_status("error", "docker-compose.yml not found")
            return False

        try:
            # Load environment variables
            env = os.environ.copy()
            if self.env_file.exists():
                with open(self.env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env[key.strip()] = value.strip()

            result = subprocess.run(
                ["docker-compose", "-f", str(docker_compose_file), "up", "-d", "neo4j"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=str(docker_compose_file.parent),
            )

            if result.returncode == 0:
                self.print_status("success", "Neo4j container started")
                self.actions_taken.append("Started Neo4j container")

                # Wait for Neo4j to be ready
                time.sleep(5)
                return self.test_neo4j_connection()
            else:
                self.print_status("error", f"Failed to start Neo4j: {result.stderr}")
                return False

        except Exception as e:
            self.print_status("error", f"Error starting Neo4j: {e}")
            return False

    def check_mcp_service(self) -> bool:
        """Check if MCP service is running with Neo4j backend."""
        self.print_section("MCP Service Check")

        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=2)

            if response.status_code == 200:
                health = response.json()

                # Check if using Neo4j
                if "neo4j" in health and health["neo4j"] == "connected":
                    self.print_status(
                        "success", "MCP service is running with Neo4j backend"
                    )
                    return True
                elif "sqlite_backend" in str(health):
                    self.print_status(
                        "warning",
                        "MCP service is running but using SQLite instead of Neo4j",
                    )
                    self.issues_found.append("MCP using SQLite instead of Neo4j")
                    return self.restart_mcp_with_neo4j()
                else:
                    self.print_status("success", "MCP service is running")
                    return True
            else:
                # Non-200 status code
                self.print_status(
                    "warning", f"MCP service returned status {response.status_code}"
                )
                self.issues_found.append(
                    f"MCP service returned status {response.status_code}"
                )
                return self.start_mcp_service()

        except Exception:
            self.print_status("warning", "MCP service is not running")
            self.issues_found.append("MCP service not running")
            return self.start_mcp_service()

    def restart_mcp_with_neo4j(self) -> bool:
        """Restart MCP service to use Neo4j backend."""
        self.print_status("action", "Restarting MCP service with Neo4j backend...")

        # Kill existing MCP service
        try:
            subprocess.run(["pkill", "-f", "mcp"], timeout=5)
            time.sleep(2)
        except Exception:
            pass

        return self.start_mcp_service()

    def start_mcp_service(self) -> bool:
        """Start the MCP service with Neo4j backend."""
        self.print_status("action", "Starting MCP service with Neo4j backend...")

        mcp_script = (
            self.gadugi_root / ".gadugi/src/src/services/mcp/start_neo4j_mcp.py"
        )

        if not mcp_script.exists():
            self.print_status("error", f"MCP start script not found at {mcp_script}")
            return False

        try:
            # Set environment variables
            env = os.environ.copy()
            env.update(
                {
                    "NEO4J_URI": "bolt://localhost:7689",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "gadugi-password",
                    "NEO4J_DATABASE": "neo4j",
                }
            )

            # Start MCP service in background
            subprocess.Popen(
                [sys.executable, str(mcp_script)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(mcp_script.parent),
            )

            # Wait for service to start
            time.sleep(5)

            # Verify it's running
            try:
                import requests

                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    self.print_status("success", "MCP service started successfully")
                    self.actions_taken.append("Started MCP service with Neo4j backend")
                    return True
            except Exception:
                pass

            self.print_status("error", "MCP service failed to start properly")
            return False

        except Exception as e:
            self.print_status("error", f"Error starting MCP service: {e}")
            return False

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary for Claude Code."""
        summary = {
            "status": "success" if not self.issues_found else "issues_found",
            "issues_found": self.issues_found,
            "actions_taken": self.actions_taken,
            "services": {
                "neo4j": "running" if self.test_neo4j_connection() else "down",
                "mcp": "running"
                if self.check_service_health("http://localhost:8000/health")
                else "down",
            },
            "recommendations": [],
        }

        if self.issues_found:
            if "Neo4j" in str(self.issues_found):
                summary["recommendations"].append(
                    "Check Docker and Neo4j container logs"
                )
            if "MCP" in str(self.issues_found):
                summary["recommendations"].append(
                    "Check MCP service logs in /tmp/neo4j-mcp.log"
                )

        return summary

    def check_service_health(self, url: str) -> bool:
        """Quick health check for a service."""
        try:
            import requests

            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def run(self) -> int:
        """Run the complete service check and management flow."""
        self.print_header()

        # Step 1: Check and fix .env configuration
        env_ok = self.check_env_file()

        # Step 2: Check and start Neo4j
        neo4j_ok = self.check_neo4j()

        # Step 3: Check and start MCP service
        mcp_ok = self.check_mcp_service()

        # Print summary
        self.print_section("Summary")

        # Report overall status
        all_ok = env_ok and neo4j_ok and mcp_ok
        if all_ok:
            self.print_status("success", "All services are running correctly")
        else:
            if not env_ok:
                self.print_status("error", "Environment configuration has issues")
            if not neo4j_ok:
                self.print_status("error", "Neo4j service has issues")
            if not mcp_ok:
                self.print_status("error", "MCP service has issues")

        if self.actions_taken:
            self.print_status("info", "Actions taken:")
            for action in self.actions_taken:
                print(f"  • {action}")

        if self.issues_found:
            self.print_status("warning", "Issues found:")
            for issue in self.issues_found:
                print(f"  • {issue}")

        if not self.issues_found:
            self.print_status(
                "success", "All services are properly configured and running!"
            )
        else:
            self.print_status(
                "warning",
                f"Found {len(self.issues_found)} issue(s) - some were auto-fixed",
            )

        # Generate output for Claude Code
        summary = self.generate_summary()

        # Output JSON for Claude Code hook
        print(
            "\n"
            + json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": f"Service check completed. Status: {summary['status']}. "
                        + f"Services: Neo4j={summary['services']['neo4j']}, "
                        + f"MCP={summary['services']['mcp']}. "
                        + (
                            f"Actions: {', '.join(self.actions_taken)}"
                            if self.actions_taken
                            else ""
                        ),
                    }
                }
            )
        )

        return 0 if not self.issues_found else 1


def main():
    """Main entry point."""
    try:
        manager = ServiceManager()
        return manager.run()
    except KeyboardInterrupt:
        print("\n\nService check interrupted by user")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.NC}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
