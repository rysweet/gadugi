#!/usr/bin/env python3
"""Simple service status checker for Gadugi v0.3"""

import socket
import subprocess
import json
import sys
from datetime import datetime

def check_port(host, port, timeout=2):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_docker_container(container_name):
    """Check if Docker container is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
            capture_output=True, text=True, timeout=5
        )
        return 'Up' in result.stdout
    except:
        return False

def get_service_status():
    """Get status of all Gadugi services"""
    services = {
        'neo4j': {
            'name': 'Neo4j Database',
            'status': False,
            'details': '',
            'ports': [7474, 7687]
        },
        'memory': {
            'name': 'Memory Service',
            'status': False,
            'details': '',
            'ports': [5000]
        },
        'event_router': {
            'name': 'Event Router',
            'status': False,
            'details': '',
            'ports': [8000]
        }
    }

    # Check Neo4j
    if check_docker_container('gadugi-neo4j'):
        if check_port('localhost', 7474) and check_port('localhost', 7687):
            services['neo4j']['status'] = True
            services['neo4j']['details'] = 'Running (Ports 7474/7687)'
        else:
            services['neo4j']['details'] = 'Container running but ports not accessible'
    else:
        services['neo4j']['details'] = 'Container not running'

    # Check Memory Service
    if check_port('localhost', 5000):
        services['memory']['status'] = True
        services['memory']['details'] = 'Running (Port 5000)'
    else:
        services['memory']['details'] = 'Not running (Fallback: SQLite/Markdown)'

    # Check Event Router
    if check_port('localhost', 8000):
        services['event_router']['status'] = True
        services['event_router']['details'] = 'Running (Port 8000)'
    else:
        services['event_router']['details'] = 'Not running'

    return services

def print_status(services):
    """Print formatted status"""
    print("\n" + "="*50)
    print("## Gadugi v0.3 Services Status")
    print("="*50)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print("\n### Core Services:")

    all_running = True
    for key, service in services.items():
        icon = "✅" if service['status'] else "❌"
        print(f"{icon} {service['name']}: {service['details']}")
        if not service['status']:
            all_running = False

    print("\n### Overall Status:", end=" ")
    if all_running:
        print("✅ FULLY OPERATIONAL")
    elif any(s['status'] for s in services.values()):
        print("⚠️  PARTIALLY OPERATIONAL")
    else:
        print("❌ NOT OPERATIONAL")

    print("="*50 + "\n")

    return 0 if all_running else 1

if __name__ == "__main__":
    try:
        services = get_service_status()

        if '--json' in sys.argv:
            print(json.dumps(services, indent=2))
            sys.exit(0)
        else:
            sys.exit(print_status(services))
    except Exception as e:
        print(f"Error checking services: {e}", file=sys.stderr)
        sys.exit(1)
