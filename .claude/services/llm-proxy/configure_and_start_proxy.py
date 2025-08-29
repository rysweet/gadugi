#!/usr/bin/env python3
"""
Complete LLM Proxy Configuration and Management Tool.

This tool combines:
1. Interactive configuration wizard
2. Claude-code-proxy HTTP server management
3. Scheduling for automatic shutdown
4. Transparent proxy support for Claude Code CLI
"""

import os
import sys
import json
import subprocess
import time
import signal
import atexit
import threading
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx

# Configuration paths
CONFIG_FILE = Path(__file__).parent / ".env"
PROXY_PID_FILE = Path.home() / ".claude-proxy.pid"
SCHEDULER_PID_FILE = Path.home() / ".claude-proxy-scheduler.pid"
PROXY_PORT = 8082
PROXY_HOST = "127.0.0.1"
PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}"

class LLMProxyManager:
    """Manages the LLM Proxy service with scheduling."""

    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self.load_config()

    def load_config(self) -> Dict[str, str]:
        """Load configuration from .env file."""
        config = {}
        if self.config_file.exists():
            with open(self.config_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        config[key] = value
        return config

    def save_config(self):
        """Save configuration to .env file."""
        lines = []
        lines.append("# LLM Proxy Configuration")
        lines.append(f"# Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Group configurations
        providers = ['OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'GOOGLE', 'OLLAMA']
        provider_keys = {}
        other_keys = {}

        for key, value in self.config.items():
            found = False
            for provider in providers:
                if key.startswith(provider):
                    if provider not in provider_keys:
                        provider_keys[provider] = {}
                    provider_keys[provider][key] = value
                    found = True
                    break
            if not found:
                other_keys[key] = value

        # Write provider configurations
        for provider in providers:
            if provider in provider_keys:
                lines.append(f"# {provider.replace('_', ' ').title()} Configuration")
                for key, value in sorted(provider_keys[provider].items()):
                    lines.append(f'{key}="{value}"')
                lines.append("")

        # Write other configurations
        if other_keys:
            lines.append("# Other Configuration")
            for key, value in sorted(other_keys.items()):
                lines.append(f'{key}="{value}"')
            lines.append("")

        self.config_file.write_text('\n'.join(lines))
        print(f"✅ Configuration saved to {self.config_file}")

    def configure_provider(self):
        """Interactive configuration wizard for LLM providers."""
        print("\n🔧 LLM Proxy Configuration Wizard")
        print("-" * 40)

        providers = {
            '1': 'OpenAI',
            '2': 'Azure OpenAI',
            '3': 'Anthropic',
            '4': 'Google',
            '5': 'Ollama (Local)',
            '6': 'Custom OpenAI-compatible'
        }

        print("\nSelect your LLM provider:")
        for key, name in providers.items():
            print(f"  {key}. {name}")

        choice = input("\nChoice (1-6): ").strip()

        if choice == '1':
            self._configure_openai()
        elif choice == '2':
            self._configure_azure()
        elif choice == '3':
            self._configure_anthropic()
        elif choice == '4':
            self._configure_google()
        elif choice == '5':
            self._configure_ollama()
        elif choice == '6':
            self._configure_custom()
        else:
            print("❌ Invalid choice")
            return False

        self.save_config()
        return True

    def _configure_azure(self):
        """Configure Azure OpenAI."""
        print("\n📋 Azure OpenAI Configuration")

        # API Key
        key = input("Azure OpenAI API Key: ").strip()
        if not key:
            print("❌ API key is required")
            return
        self.config['AZURE_OPENAI_API_KEY'] = key

        # Endpoint
        endpoint = input("Azure OpenAI Endpoint (e.g., https://your-resource.openai.azure.com): ").strip()
        if not endpoint:
            print("❌ Endpoint is required")
            return
        self.config['AZURE_OPENAI_ENDPOINT'] = endpoint.rstrip('/')

        # Deployment name
        deployment = input("Deployment Name (e.g., gpt-4): ").strip()
        if not deployment:
            print("❌ Deployment name is required")
            return
        self.config['AZURE_OPENAI_DEPLOYMENT_NAME'] = deployment

        # API Version (optional)
        version = input("API Version (default: 2024-02-15-preview): ").strip()
        self.config['AZURE_API_VERSION'] = version or "2024-02-15-preview"

        # Map to OpenAI settings for proxy
        self.config['OPENAI_API_KEY'] = key
        self.config['OPENAI_BASE_URL'] = f"{endpoint}/openai/deployments/{deployment}"
        self.config['BIG_MODEL'] = deployment
        self.config['MIDDLE_MODEL'] = deployment
        self.config['SMALL_MODEL'] = deployment

        print("✅ Azure OpenAI configured")

    def _configure_openai(self):
        """Configure OpenAI."""
        print("\n📋 OpenAI Configuration")

        key = input("OpenAI API Key (sk-...): ").strip()
        if not key:
            print("❌ API key is required")
            return
        self.config['OPENAI_API_KEY'] = key
        self.config['OPENAI_BASE_URL'] = "https://api.openai.com/v1"

        # Model selection
        print("\nModel Configuration:")
        big = input("Big model (default: gpt-4o): ").strip() or "gpt-4o"
        small = input("Small model (default: gpt-4o-mini): ").strip() or "gpt-4o-mini"

        self.config['BIG_MODEL'] = big
        self.config['MIDDLE_MODEL'] = big  # Same as big by default
        self.config['SMALL_MODEL'] = small

        print("✅ OpenAI configured")

    def _configure_anthropic(self):
        """Configure Anthropic (direct, not through proxy)."""
        print("\n📋 Anthropic Configuration")
        print("⚠️  Note: This configures direct Anthropic access, not proxy routing")

        key = input("Anthropic API Key: ").strip()
        if not key:
            print("❌ API key is required")
            return
        self.config['ANTHROPIC_API_KEY'] = key
        print("✅ Anthropic configured")

    def _configure_google(self):
        """Configure Google AI."""
        print("\n📋 Google AI Configuration")
        print("⚠️  Google AI support requires additional setup")

        key = input("Google AI API Key: ").strip()
        if not key:
            print("❌ API key is required")
            return
        self.config['GOOGLE_API_KEY'] = key
        print("✅ Google AI configured (requires custom implementation)")

    def _configure_ollama(self):
        """Configure Ollama (local models)."""
        print("\n📋 Ollama Configuration")

        host = input("Ollama host (default: localhost): ").strip() or "localhost"
        port = input("Ollama port (default: 11434): ").strip() or "11434"

        self.config['OPENAI_API_KEY'] = "ollama"  # Dummy key
        self.config['OPENAI_BASE_URL'] = f"http://{host}:{port}/v1"

        print("\nModel Configuration:")
        big = input("Big model (e.g., llama3.1:70b): ").strip() or "llama3.1:70b"
        small = input("Small model (e.g., llama3.1:8b): ").strip() or "llama3.1:8b"

        self.config['BIG_MODEL'] = big
        self.config['MIDDLE_MODEL'] = big
        self.config['SMALL_MODEL'] = small

        print("✅ Ollama configured")

    def _configure_custom(self):
        """Configure custom OpenAI-compatible endpoint."""
        print("\n📋 Custom OpenAI-compatible Configuration")

        base_url = input("API Base URL: ").strip()
        if not base_url:
            print("❌ Base URL is required")
            return
        self.config['OPENAI_BASE_URL'] = base_url

        key = input("API Key (or 'dummy' if not required): ").strip()
        if not key:
            print("❌ API key is required")
            return
        self.config['OPENAI_API_KEY'] = key

        print("\nModel Configuration:")
        big = input("Big model name: ").strip()
        small = input("Small model name: ").strip()

        if not big or not small:
            print("❌ Model names are required")
            return

        self.config['BIG_MODEL'] = big
        self.config['MIDDLE_MODEL'] = big
        self.config['SMALL_MODEL'] = small

        print("✅ Custom provider configured")

    def is_proxy_running(self) -> bool:
        """Check if proxy is already running."""
        if PROXY_PID_FILE.exists():
            try:
                pid = int(PROXY_PID_FILE.read_text())
                if psutil.pid_exists(pid):
                    try:
                        proc = psutil.Process(pid)
                        if "python" in proc.name().lower():
                            return True
                    except:
                        pass
            except:
                pass
        return False

    def start_proxy(self) -> bool:
        """Start the claude-code-proxy server."""
        if self.is_proxy_running():
            print("✅ Proxy already running")
            return True

        print("🚀 Starting LLM Proxy server...")

        # Check configuration
        if not self.config.get('OPENAI_API_KEY') and not self.config.get('AZURE_OPENAI_API_KEY'):
            print("❌ No API key configured. Run with --configure first.")
            return False

        # Set up environment
        env = os.environ.copy()
        env.update(self.config)

        # Add proxy-specific settings
        env['HOST'] = PROXY_HOST
        env['PORT'] = str(PROXY_PORT)
        env['LOG_LEVEL'] = 'WARNING'

        # Start proxy server
        proxy_script = Path(__file__).parent / "claude-code-proxy" / "start_proxy.py"
        if not proxy_script.exists():
            print(f"❌ Proxy script not found at {proxy_script}")
            return False

        # Start process
        log_file = Path.home() / ".claude-proxy.log"
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                [sys.executable, str(proxy_script)],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        # Save PID
        PROXY_PID_FILE.write_text(str(process.pid))

        # Wait for server to start
        print("⏳ Waiting for proxy to start...")
        for i in range(30):
            try:
                response = httpx.get(f"{PROXY_URL}/health", timeout=1)
                if response.status_code == 200:
                    print(f"✅ Proxy server started on {PROXY_URL}")
                    print(f"📝 Logs: {log_file}")
                    return True
            except:
                pass
            time.sleep(1)

        print("❌ Proxy failed to start. Check logs at:", log_file)
        self.stop_proxy()
        return False

    def stop_proxy(self):
        """Stop the proxy server."""
        stopped = False

        # Stop main proxy
        if PROXY_PID_FILE.exists():
            try:
                pid = int(PROXY_PID_FILE.read_text())
                os.kill(pid, signal.SIGTERM)
                PROXY_PID_FILE.unlink()
                print("🛑 Proxy stopped")
                stopped = True
            except:
                pass

        # Stop scheduler if running
        if SCHEDULER_PID_FILE.exists():
            try:
                pid = int(SCHEDULER_PID_FILE.read_text())
                os.kill(pid, signal.SIGTERM)
                SCHEDULER_PID_FILE.unlink()
                print("🛑 Scheduler stopped")
                stopped = True
            except:
                pass

        if not stopped:
            print("❌ No proxy running")

    def start_with_schedule(self):
        """Start proxy with scheduled shutdown."""
        if not self.start_proxy():
            return False

        print("\n⏰ Schedule Configuration")
        print("Options:")
        print("  1. Run until specific time today (e.g., 7:00 PM)")
        print("  2. Run for duration (e.g., 2 hours)")
        print("  3. Run until tomorrow at specific time")
        print("  4. No schedule (run indefinitely)")

        choice = input("\nChoice (1-4): ").strip()

        if choice == '1':
            shutdown_time = self._get_shutdown_time_today()
        elif choice == '2':
            shutdown_time = self._get_shutdown_time_duration()
        elif choice == '3':
            shutdown_time = self._get_shutdown_time_tomorrow()
        else:
            print("✅ Proxy running without schedule")
            return True

        if shutdown_time:
            self._schedule_shutdown(shutdown_time)

        return True

    def _get_shutdown_time_today(self) -> Optional[datetime]:
        """Get shutdown time for today."""
        time_str = input("Shutdown time (e.g., 19:00 or 7:00 PM): ").strip()

        try:
            # Try 24-hour format
            if ':' in time_str and len(time_str.split(':')[0]) <= 2:
                hour, minute = time_str.replace('PM', '').replace('AM', '').strip().split(':')
                hour = int(hour)
                minute = int(minute)

                # Handle PM notation
                if 'PM' in time_str.upper() and hour < 12:
                    hour += 12
                elif 'AM' in time_str.upper() and hour == 12:
                    hour = 0

                now = datetime.now()
                shutdown = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if shutdown <= now:
                    print("❌ Time has already passed today")
                    return None

                return shutdown
        except:
            print("❌ Invalid time format")
            return None

    def _get_shutdown_time_duration(self) -> Optional[datetime]:
        """Get shutdown time based on duration."""
        duration_str = input("Duration (e.g., 2h, 30m, 2h30m): ").strip()

        try:
            hours = 0
            minutes = 0

            if 'h' in duration_str:
                parts = duration_str.split('h')
                hours = int(parts[0])
                if len(parts) > 1 and parts[1]:
                    minutes = int(parts[1].replace('m', ''))
            elif 'm' in duration_str:
                minutes = int(duration_str.replace('m', ''))
            else:
                hours = float(duration_str)

            if hours == 0 and minutes == 0:
                print("❌ Invalid duration")
                return None

            return datetime.now() + timedelta(hours=hours, minutes=minutes)
        except:
            print("❌ Invalid duration format")
            return None

    def _get_shutdown_time_tomorrow(self) -> Optional[datetime]:
        """Get shutdown time for tomorrow."""
        time_str = input("Tomorrow's shutdown time (e.g., 09:00): ").strip()

        try:
            hour, minute = time_str.split(':')
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        except:
            print("❌ Invalid time format")
            return None

    def _schedule_shutdown(self, shutdown_time: datetime):
        """Schedule automatic shutdown."""
        print(f"\n⏰ Scheduling shutdown for {shutdown_time.strftime('%Y-%m-%d %H:%M')}")

        # Create scheduler script
        scheduler_script = f"""
import os
import signal
import time
from datetime import datetime

shutdown_time = datetime.fromisoformat('{shutdown_time.isoformat()}')
pid = {PROXY_PID_FILE.read_text()}

while datetime.now() < shutdown_time:
    time.sleep(60)  # Check every minute

# Shutdown time reached
try:
    os.kill(int(pid), signal.SIGTERM)
    print(f"Proxy stopped at scheduled time: {{shutdown_time}}")
except:
    pass

# Clean up PID files
for f in ['{PROXY_PID_FILE}', '{SCHEDULER_PID_FILE}']:
    try:
        os.unlink(f)
    except:
        pass
"""

        # Write and execute scheduler
        scheduler_file = Path.home() / ".claude-proxy-scheduler.py"
        scheduler_file.write_text(scheduler_script)

        # Start scheduler in background
        process = subprocess.Popen(
            [sys.executable, str(scheduler_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        SCHEDULER_PID_FILE.write_text(str(process.pid))

        time_diff = shutdown_time - datetime.now()
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)

        print(f"✅ Scheduler started - will shutdown in {hours}h {minutes}m")

    def status(self):
        """Check proxy status."""
        if self.is_proxy_running():
            print("✅ Proxy is running")
            print(f"   URL: {PROXY_URL}")

            # Check scheduler
            if SCHEDULER_PID_FILE.exists():
                print("⏰ Scheduled shutdown is active")

            # Show configuration
            if self.config.get('AZURE_OPENAI_ENDPOINT'):
                print(f"   Provider: Azure OpenAI")
                print(f"   Endpoint: {self.config['AZURE_OPENAI_ENDPOINT']}")
            elif self.config.get('OPENAI_BASE_URL'):
                if 'ollama' in self.config['OPENAI_BASE_URL'].lower():
                    print(f"   Provider: Ollama (Local)")
                elif 'openai.com' in self.config['OPENAI_BASE_URL']:
                    print(f"   Provider: OpenAI")
                else:
                    print(f"   Provider: Custom")
                print(f"   Base URL: {self.config['OPENAI_BASE_URL']}")
        else:
            print("❌ Proxy is not running")
            print(f"   Start with: {sys.argv[0]} --start")

    def test_connection(self):
        """Test the proxy connection with detailed health check."""
        if not self.is_proxy_running():
            print("❌ Proxy is not running. Start it first.")
            print("   Run: uv run python configure_and_start_proxy.py --start")
            return

        print(f"\n🧪 Testing LLM Proxy Service")
        print("=" * 50)

        try:
            # Test health endpoint with detailed reporting
            print("\n📊 Health Check Results:")
            response = httpx.get(f"{PROXY_URL}/health", timeout=10)
            health_data = response.json()

            # Display configuration
            print(f"\n🔧 Configuration:")
            print(f"   Provider: {health_data['configuration']['provider']}")
            print(f"   Endpoint: {health_data['configuration']['endpoint']}")
            print(f"   Models:")
            print(f"     - Big: {health_data['configuration']['models']['big']}")
            print(f"     - Middle: {health_data['configuration']['models']['middle']}")
            print(f"     - Small: {health_data['configuration']['models']['small']}")

            # Display proxy status
            print(f"\n🚦 Status:")
            proxy_icon = "✅" if health_data['proxy_status'] == "healthy" else "⚠️" if health_data['proxy_status'] == "degraded" else "❌"
            print(f"   Proxy: {proxy_icon} {health_data['proxy_status']}")

            upstream_icon = "✅" if health_data['upstream_status'] == "healthy" else "⚠️" if health_data['upstream_status'] in ["warning", "assumed-healthy"] else "❌"
            print(f"   Upstream: {upstream_icon} {health_data['upstream_status']}")

            # Display errors if any
            if health_data.get('errors'):
                print(f"\n❌ Errors Found:")
                for error in health_data['errors']:
                    print(f"   • {error}")

            # Display instructions if any
            if health_data.get('instructions'):
                print(f"\n📝 Instructions to Fix:")
                for instruction in health_data['instructions']:
                    if instruction:  # Skip empty lines
                        print(f"   {instruction}")

            # Only test actual API if upstream is healthy
            if health_data['upstream_status'] in ["healthy", "assumed-healthy"]:
                print("\n🔄 Testing API Call...")

                test_message = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [
                        {"role": "user", "content": "Reply with 'test ok' only"}
                    ]
                }

                headers = {}
                if self.config.get('ANTHROPIC_API_KEY'):
                    headers['x-api-key'] = self.config['ANTHROPIC_API_KEY']
                else:
                    headers['x-api-key'] = 'test-key'

                try:
                    response = httpx.post(
                        f"{PROXY_URL}/v1/messages",
                        json=test_message,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        print("   ✅ API call successful")
                        result = response.json()
                        if 'content' in result and result['content']:
                            response_text = result['content'][0].get('text', 'No text')[:100]
                            print(f"   Response: \"{response_text}\"")
                    else:
                        print(f"   ❌ API call failed: {response.status_code}")
                        error_data = response.json()
                        if 'detail' in error_data:
                            print(f"   Error: {error_data['detail']}")
                except Exception as e:
                    print(f"   ❌ API test failed: {str(e)}")

                print("\n✨ Summary:")
                if health_data['upstream_status'] == "healthy":
                    print("   Your LLM Proxy is fully operational!")
                    print("   You can now use: ANTHROPIC_BASE_URL=http://localhost:8082 claude")
                else:
                    print("   Proxy is running but needs configuration fixes.")
            else:
                print("\n⚠️  Skipping API test - upstream configuration needs to be fixed first")
                print("\n💡 Next Steps:")
                print("   1. Fix the configuration issues listed above")
                print("   2. Restart the proxy: uv run python configure_and_start_proxy.py --stop && --start")
                print("   3. Run this test again: uv run python configure_and_start_proxy.py --test")

        except httpx.ConnectError:
            print("❌ Cannot connect to proxy at", PROXY_URL)
            print("   Is the proxy running? Check with: uv run python configure_and_start_proxy.py --status")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print("   Check logs at: ~/.claude-proxy.log")

def main():
    """Main entry point."""
    manager = LLMProxyManager()

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--configure':
            manager.configure_provider()
        elif command == '--start':
            manager.start_proxy()
        elif command == '--start-scheduled':
            manager.start_with_schedule()
        elif command == '--stop':
            manager.stop_proxy()
        elif command == '--status':
            manager.status()
        elif command == '--test':
            manager.test_connection()
        elif command == '--help':
            print("LLM Proxy Manager for Claude Code")
            print("\nCommands:")
            print("  --configure        : Configure LLM provider")
            print("  --start           : Start proxy server")
            print("  --start-scheduled : Start with automatic shutdown")
            print("  --stop            : Stop proxy server")
            print("  --status          : Check proxy status")
            print("  --test            : Test proxy connection")
            print("\nUsage with Claude:")
            print("  1. Configure: python configure_and_start_proxy.py --configure")
            print("  2. Start: python configure_and_start_proxy.py --start")
            print("  3. Use: ANTHROPIC_BASE_URL=http://localhost:8082 claude")
        else:
            print(f"Unknown command: {command}")
            print("Use --help for available commands")
    else:
        # Interactive mode
        print("🤖 LLM Proxy Manager")
        print("\nOptions:")
        print("  1. Configure provider")
        print("  2. Start proxy")
        print("  3. Start with schedule")
        print("  4. Stop proxy")
        print("  5. Check status")
        print("  6. Test connection")
        print("  7. Exit")

        while True:
            choice = input("\nChoice (1-7): ").strip()

            if choice == '1':
                manager.configure_provider()
            elif choice == '2':
                manager.start_proxy()
            elif choice == '3':
                manager.start_with_schedule()
            elif choice == '4':
                manager.stop_proxy()
            elif choice == '5':
                manager.status()
            elif choice == '6':
                manager.test_connection()
            elif choice == '7':
                break
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()
