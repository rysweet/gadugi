#!/usr/bin/env python3
"""
Daemon script for Event Router service.
Can start, stop, and check status of the Event Router service.
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path

SERVICE_DIR = Path(__file__).parent
PID_FILE = SERVICE_DIR / "logs" / "event-router.pid"
LOG_FILE = SERVICE_DIR / "logs" / "event-router.log"

def get_pid():
    """Get PID of running service if any."""
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is still running
            os.kill(pid, 0)
            return pid
        except (OSError, ValueError):
            # Process no longer exists or invalid PID
            PID_FILE.unlink(missing_ok=True)
    return None

def start_service():
    """Start the Event Router service."""
    if get_pid():
        print("❌ Event Router service is already running")
        return False

    print("🚀 Starting Event Router service...")

    # Ensure directories exist
    os.makedirs(SERVICE_DIR / "logs", exist_ok=True)

    # Start the service
    with open(LOG_FILE, 'w') as log:
        process = subprocess.Popen(
            [sys.executable, str(SERVICE_DIR / "start_event_router.py")],
            cwd=str(SERVICE_DIR),
            stdout=log,
            stderr=log,
            start_new_session=True
        )

    # Save PID
    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))

    # Wait a moment and check if service started successfully
    time.sleep(2)

    if get_pid():
        print("✅ Event Router service started successfully")
        print(f"📋 PID: {process.pid}")
        print(f"📝 Logs: {LOG_FILE}")
        print("🌐 Service URL: http://localhost:8000")
        print("💓 Health check: curl http://localhost:8000/health")
        return True
    else:
        print("❌ Failed to start Event Router service")
        print(f"📝 Check logs: {LOG_FILE}")
        return False

def stop_service():
    """Stop the Event Router service."""
    pid = get_pid()
    if not pid:
        print("❌ Event Router service is not running")
        return False

    print(f"🛑 Stopping Event Router service (PID: {pid})...")

    try:
        # Try graceful shutdown first
        os.kill(pid, signal.SIGTERM)

        # Wait for process to exit
        for _ in range(10):
            time.sleep(1)
            try:
                os.kill(pid, 0)
            except OSError:
                # Process has exited
                break
        else:
            # Force kill if still running
            print("⚠️  Process didn't exit gracefully, forcing...")
            os.kill(pid, signal.SIGKILL)

        PID_FILE.unlink(missing_ok=True)
        print("✅ Event Router service stopped")
        return True

    except OSError:
        print("❌ Failed to stop service (process may have already exited)")
        PID_FILE.unlink(missing_ok=True)
        return False

def status_service():
    """Check status of the Event Router service."""
    pid = get_pid()
    if pid:
        print(f"✅ Event Router service is running (PID: {pid})")
        print("🌐 Service URL: http://localhost:8000")
        print("💓 Health check: curl http://localhost:8000/health")

        # Try to get actual health status
        try:
            import urllib.request
            import json

            with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as response:
                if response.status == 200:
                    health_data = json.loads(response.read().decode())
                    print(f"💚 Health status: {health_data.get('status', 'unknown')}")
                else:
                    print(f"⚠️  Health check returned status: {response.status}")
        except Exception as e:
            print(f"⚠️  Health check failed: {e}")

        return True
    else:
        print("❌ Event Router service is not running")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python daemon.py {start|stop|status|restart}")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "start":
        success = start_service()
    elif action == "stop":
        success = stop_service()
    elif action == "status":
        success = status_service()
    elif action == "restart":
        print("🔄 Restarting Event Router service...")
        stop_service()
        time.sleep(1)
        success = start_service()
    else:
        print(f"❌ Unknown action: {action}")
        print("Usage: python daemon.py {start|stop|status|restart}")
        sys.exit(1)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
