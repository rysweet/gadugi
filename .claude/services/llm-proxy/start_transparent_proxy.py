#!/usr/bin/env python3
"""
Transparent LLM Proxy launcher for Claude Code.

This script:
1. Starts the claude-code-proxy server in the background
2. Launches Claude Code with the proxy environment variables
3. Makes the proxy usage completely transparent to the user
"""

import os
import sys
import subprocess
import time
import signal
import atexit
from pathlib import Path
import json
import psutil

# Configuration
PROXY_PORT = 8082
PROXY_HOST = "127.0.0.1"
PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}"
PROXY_PID_FILE = Path.home() / ".claude-proxy.pid"
CONFIG_FILE = Path(__file__).parent / ".env"

def load_config():
    """Load configuration from .env file."""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    config[key] = value
    return config

def is_proxy_running():
    """Check if proxy is already running."""
    if PROXY_PID_FILE.exists():
        try:
            pid = int(PROXY_PID_FILE.read_text())
            # Check if process exists
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

def start_proxy():
    """Start the claude-code-proxy server."""
    if is_proxy_running():
        print("✅ Proxy already running")
        return True
    
    print("🚀 Starting LLM Proxy server...")
    
    # Load configuration
    config = load_config()
    if not config.get('OPENAI_API_KEY') and not config.get('AZURE_OPENAI_API_KEY'):
        print("❌ No API key configured. Run configure_proxy.py first.")
        return False
    
    # Set up environment
    env = os.environ.copy()
    env.update(config)
    
    # Add proxy-specific settings
    env['HOST'] = PROXY_HOST
    env['PORT'] = str(PROXY_PORT)
    env['LOG_LEVEL'] = 'WARNING'
    
    # Map Azure settings to OpenAI settings if using Azure
    if config.get('AZURE_OPENAI_API_KEY'):
        env['OPENAI_API_KEY'] = config['AZURE_OPENAI_API_KEY']
        env['OPENAI_BASE_URL'] = f"{config['AZURE_OPENAI_ENDPOINT']}/openai/deployments/{config['AZURE_OPENAI_DEPLOYMENT_NAME']}"
        env['BIG_MODEL'] = config.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        env['MIDDLE_MODEL'] = config.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        env['SMALL_MODEL'] = config.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
    
    # Start proxy server
    proxy_script = Path(__file__).parent / "claude-code-proxy" / "src" / "main.py"
    if not proxy_script.exists():
        print(f"❌ Proxy script not found at {proxy_script}")
        return False
    
    process = subprocess.Popen(
        [sys.executable, str(proxy_script)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Save PID
    PROXY_PID_FILE.write_text(str(process.pid))
    
    # Wait for server to start
    print("⏳ Waiting for proxy to start...")
    for i in range(30):  # 30 second timeout
        try:
            import httpx
            response = httpx.get(f"{PROXY_URL}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Proxy server started successfully")
                return True
        except:
            pass
        time.sleep(1)
    
    # If we get here, proxy didn't start
    print("❌ Proxy failed to start")
    stop_proxy()
    return False

def stop_proxy():
    """Stop the proxy server."""
    if PROXY_PID_FILE.exists():
        try:
            pid = int(PROXY_PID_FILE.read_text())
            os.kill(pid, signal.SIGTERM)
            PROXY_PID_FILE.unlink()
            print("🛑 Proxy stopped")
        except:
            pass

def launch_claude():
    """Launch Claude Code with proxy environment."""
    print("\n🎯 Launching Claude Code with transparent proxy...")
    print(f"   Proxy URL: {PROXY_URL}")
    print(f"   All LLM calls will be routed through the proxy\n")
    
    # Set environment variables for Claude
    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    
    # Use a dummy key if not configured (proxy will use its own)
    if 'ANTHROPIC_API_KEY' not in env:
        env['ANTHROPIC_API_KEY'] = 'proxy-managed'
    
    # Launch Claude
    try:
        # Pass all original arguments to Claude
        claude_args = sys.argv[1:] if len(sys.argv) > 1 else []
        result = subprocess.run(['claude'] + claude_args, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Claude Code session ended")
        return 0
    except Exception as e:
        print(f"❌ Failed to launch Claude: {e}")
        return 1

def create_claude_wrapper():
    """Create a wrapper script that can be added to PATH."""
    wrapper_path = Path.home() / ".local" / "bin" / "claude-proxy"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    
    wrapper_content = f"""#!/bin/bash
# Claude Code with transparent LLM proxy
exec {sys.executable} {Path(__file__).absolute()} "$@"
"""
    
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)
    
    print(f"✅ Wrapper created at {wrapper_path}")
    print(f"   Add to your shell config: alias claude='claude-proxy'")
    print(f"   Or add ~/.local/bin to your PATH")

def main():
    """Main entry point."""
    # Handle special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stop':
            stop_proxy()
            return 0
        elif sys.argv[1] == '--status':
            if is_proxy_running():
                print("✅ Proxy is running")
            else:
                print("❌ Proxy is not running")
            return 0
        elif sys.argv[1] == '--install':
            create_claude_wrapper()
            return 0
        elif sys.argv[1] == '--help':
            print("Claude Code Transparent Proxy")
            print("\nUsage:")
            print("  python start_transparent_proxy.py         # Start proxy and launch Claude")
            print("  python start_transparent_proxy.py --stop  # Stop the proxy")
            print("  python start_transparent_proxy.py --status # Check proxy status")
            print("  python start_transparent_proxy.py --install # Create shell wrapper")
            print("\nThe proxy runs in the background and routes all Claude API calls")
            print("through your configured LLM provider (OpenAI, Azure, etc.)")
            return 0
    
    # Start proxy if not running
    if not is_proxy_running():
        if not start_proxy():
            return 1
    
    # Launch Claude with proxy
    return launch_claude()

if __name__ == "__main__":
    sys.exit(main())