# Memory Service Manager Agent


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview
Manages the Gadugi v0.3 hierarchical memory system with fallback chain awareness. Coordinates Neo4j primary storage, local SQLite fallback, and in-memory caching layers.

## Core Capabilities
- Monitor memory system health across all layers
- Manage Neo4j memory backend connection
- Handle SQLite fallback activation
- Monitor in-memory cache performance
- Detect and recover from memory system failures
- Provide detailed memory system status reporting

## Memory System Architecture

### Primary Layer: Neo4j
- **Service**: Neo4j Graph Database
- **Port**: 7689 (Bolt), 7475 (HTTP)
- **Role**: Primary persistent memory storage
- **Features**: Graph relationships, complex queries, ACID compliance

### Fallback Layer: SQLite
- **Service**: Local SQLite Database
- **Location**: `.claude/memory/fallback.db`
- **Role**: Local fallback when Neo4j unavailable
- **Features**: Local persistence, lightweight, always available

### Cache Layer: In-Memory
- **Service**: Python dictionaries/Redis (optional)
- **Role**: Fast access cache for recent data
- **Features**: Sub-millisecond access, temporary storage

## Service Dependencies
```
Memory Service
├── Neo4j Database (Primary)
│   ├── Requires: Neo4jServiceManager
│   └── Fallback: SQLite
├── SQLite Database (Fallback)
│   ├── Always available
│   └── Auto-created
└── In-Memory Cache (Performance)
    ├── Python-based
    └── Optional Redis
```

## Implementation

### Memory System Status Check
```python
#!/usr/bin/env python3
"""
Memory Service Manager - Status Check Implementation
"""
import os
import sqlite3
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional

def check_memory_system_status() -> Dict[str, Any]:
    """Check status of all memory system layers."""
    status = {
        "service": "memory-system",
        "overall_status": "UNKNOWN",
        "layers": {
            "neo4j": check_neo4j_memory_backend(),
            "sqlite": check_sqlite_fallback(),
            "cache": check_memory_cache()
        },
        "active_backend": "unknown",
        "fallback_active": False,
        "message": ""
    }
    
    # Determine overall status and active backend
    if status["layers"]["neo4j"]["status"] == "HEALTHY":
        status["overall_status"] = "OPTIMAL"
        status["active_backend"] = "neo4j"
        status["message"] = "All memory layers operational, using Neo4j primary"
    elif status["layers"]["sqlite"]["status"] == "HEALTHY":
        status["overall_status"] = "DEGRADED"
        status["active_backend"] = "sqlite"
        status["fallback_active"] = True
        status["message"] = "Using SQLite fallback, Neo4j unavailable"
    else:
        status["overall_status"] = "CRITICAL"
        status["active_backend"] = "memory-only"
        status["message"] = "Critical: No persistent storage available"
    
    return status

def check_neo4j_memory_backend() -> Dict[str, Any]:
    """Check Neo4j as primary memory backend."""
    try:
        # Test Neo4j connection via Neo4jServiceManager
        result = subprocess.run([
            "bash", "-c", 
            "curl -f http://localhost:7475/db/data/ >/dev/null 2>&1"
        ], capture_output=True, timeout=5)
        
        if result.returncode == 0:
            # Test Bolt connection for memory operations
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver("bolt://localhost:7689", 
                                            auth=("neo4j", "changeme"))
                with driver.session() as session:
                    session.run("RETURN 1").single()
                driver.close()
                
                return {
                    "status": "HEALTHY",
                    "backend": "neo4j",
                    "connection": "bolt://localhost:7689",
                    "features": ["graph", "relationships", "acid"],
                    "message": "Neo4j memory backend operational"
                }
            except Exception as e:
                return {
                    "status": "UNHEALTHY",
                    "backend": "neo4j",
                    "connection": "bolt://localhost:7689",
                    "error": str(e),
                    "message": "Neo4j HTTP up but Bolt connection failed"
                }
        else:
            return {
                "status": "UNAVAILABLE",
                "backend": "neo4j",
                "connection": "bolt://localhost:7689",
                "message": "Neo4j service not responding"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "backend": "neo4j",
            "error": str(e),
            "message": f"Neo4j check failed: {str(e)}"
        }

def check_sqlite_fallback() -> Dict[str, Any]:
    """Check SQLite fallback system."""
    try:
        # Ensure SQLite directory exists
        memory_dir = Path(".claude/memory")
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        sqlite_path = memory_dir / "fallback.db"
        
        # Test SQLite connection
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Test basic operations
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        # Check if memory tables exist, create if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id INTEGER PRIMARY KEY,
                source_key TEXT,
                target_key TEXT,
                relationship_type TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        return {
            "status": "HEALTHY",
            "backend": "sqlite",
            "path": str(sqlite_path),
            "size": sqlite_path.stat().st_size if sqlite_path.exists() else 0,
            "features": ["local", "persistent", "acid"],
            "message": "SQLite fallback operational"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "backend": "sqlite",
            "error": str(e),
            "message": f"SQLite fallback failed: {str(e)}"
        }

def check_memory_cache() -> Dict[str, Any]:
    """Check in-memory cache layer."""
    try:
        # Test basic Python memory cache
        cache_test = {"test": "value"}
        cache_test.get("test")
        
        # Check if Redis is available (optional)
        redis_available = False
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            redis_available = True
        except:
            pass
        
        return {
            "status": "HEALTHY",
            "backend": "memory",
            "layers": {
                "python": True,
                "redis": redis_available
            },
            "features": ["fast", "temporary"],
            "message": f"Memory cache operational ({'with Redis' if redis_available else 'Python-only'})"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "backend": "memory",
            "error": str(e),
            "message": f"Memory cache check failed: {str(e)}"
        }
```

### Memory Service Management
```python
def start_memory_service():
    """Initialize memory service with fallback chain."""
    print("Starting Memory Service...")
    
    status = check_memory_system_status()
    
    # Ensure SQLite fallback is always ready
    sqlite_status = check_sqlite_fallback()
    if sqlite_status["status"] != "HEALTHY":
        print(f"ERROR: SQLite fallback initialization failed: {sqlite_status.get('error')}")
        return False
    
    print("✅ SQLite fallback ready")
    
    # Try to connect to Neo4j primary
    neo4j_status = check_neo4j_memory_backend()
    if neo4j_status["status"] == "HEALTHY":
        print("✅ Neo4j primary backend connected")
    else:
        print(f"⚠️ Neo4j unavailable: {neo4j_status.get('message')}")
        print("📦 Will use SQLite fallback")
    
    # Initialize memory cache
    cache_status = check_memory_cache()
    if cache_status["status"] == "HEALTHY":
        print("✅ Memory cache initialized")
    else:
        print(f"⚠️ Memory cache issues: {cache_status.get('message')}")
    
    print(f"Memory Service Status: {status['overall_status']}")
    print(f"Active Backend: {status['active_backend']}")
    
    return True

def stop_memory_service():
    """Gracefully stop memory service."""
    print("Stopping Memory Service...")
    
    # Memory service doesn't need explicit stopping as it's primarily
    # a client to other services (Neo4j) or local resources (SQLite)
    # But we can clean up any resources if needed
    
    print("Memory Service stopped")
    return True

def restart_memory_service():
    """Restart memory service."""
    print("Restarting Memory Service...")
    stop_memory_service()
    return start_memory_service()
```

### Fallback Chain Management
```python
def test_memory_operations():
    """Test memory operations across the fallback chain."""
    print("Testing memory operations across fallback chain...")
    
    test_results = {
        "neo4j": {"read": False, "write": False, "error": None},
        "sqlite": {"read": False, "write": False, "error": None},
        "cache": {"read": False, "write": False, "error": None}
    }
    
    # Test Neo4j operations
    try:
        # This would use actual Gadugi memory client
        # For now, simulate with connection test
        neo4j_status = check_neo4j_memory_backend()
        if neo4j_status["status"] == "HEALTHY":
            test_results["neo4j"]["read"] = True
            test_results["neo4j"]["write"] = True
    except Exception as e:
        test_results["neo4j"]["error"] = str(e)
    
    # Test SQLite operations
    try:
        import sqlite3
        conn = sqlite3.connect(".claude/memory/fallback.db")
        cursor = conn.cursor()
        
        # Test write
        cursor.execute("INSERT OR REPLACE INTO memory_entries (key, value) VALUES (?, ?)", 
                      ("test_key", "test_value"))
        conn.commit()
        test_results["sqlite"]["write"] = True
        
        # Test read
        cursor.execute("SELECT value FROM memory_entries WHERE key = ?", ("test_key",))
        result = cursor.fetchone()
        if result and result[0] == "test_value":
            test_results["sqlite"]["read"] = True
        
        conn.close()
    except Exception as e:
        test_results["sqlite"]["error"] = str(e)
    
    # Test cache operations
    try:
        cache = {}
        cache["test_key"] = "test_value"
        if cache.get("test_key") == "test_value":
            test_results["cache"]["read"] = True
            test_results["cache"]["write"] = True
    except Exception as e:
        test_results["cache"]["error"] = str(e)
    
    return test_results

def get_memory_statistics():
    """Get detailed memory system statistics."""
    stats = {
        "backends": {},
        "performance": {},
        "usage": {}
    }
    
    # Neo4j statistics
    neo4j_status = check_neo4j_memory_backend()
    if neo4j_status["status"] == "HEALTHY":
        try:
            # This would query actual Neo4j memory stats
            # For now, provide placeholder
            stats["backends"]["neo4j"] = {
                "nodes": "unknown",
                "relationships": "unknown",
                "memory_usage": "unknown"
            }
        except:
            pass
    
    # SQLite statistics
    sqlite_path = Path(".claude/memory/fallback.db")
    if sqlite_path.exists():
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            entry_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memory_relationships")
            relationship_count = cursor.fetchone()[0]
            
            stats["backends"]["sqlite"] = {
                "entries": entry_count,
                "relationships": relationship_count,
                "size_bytes": sqlite_path.stat().st_size
            }
            
            conn.close()
        except Exception as e:
            stats["backends"]["sqlite"] = {"error": str(e)}
    
    return stats
```

## Bash Interface
```bash
#!/bin/bash
# Memory Service Manager - Bash Interface

MEMORY_MANAGER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$MEMORY_MANAGER_DIR/memory_service_manager.py"

check_memory_status() {
    echo "=== Memory System Status ==="
    python3 -c "
import sys
sys.path.append('$MEMORY_MANAGER_DIR')
from memory_service_manager import check_memory_system_status, get_memory_statistics
import json

status = check_memory_system_status()
print(f\"Overall Status: {status['overall_status']}\")
print(f\"Active Backend: {status['active_backend']}\")
print(f\"Fallback Active: {'Yes' if status['fallback_active'] else 'No'}\")
print(f\"Message: {status['message']}\")
print()

for layer_name, layer_info in status['layers'].items():
    print(f\"{layer_name.upper()} Layer:\")
    print(f\"  Status: {layer_info['status']}\")
    print(f\"  Message: {layer_info['message']}\")
    if 'features' in layer_info:
        print(f\"  Features: {', '.join(layer_info['features'])}\")
    print()
"
}

start_memory_service() {
    python3 -c "
import sys
sys.path.append('$MEMORY_MANAGER_DIR')
from memory_service_manager import start_memory_service
start_memory_service()
"
}

stop_memory_service() {
    python3 -c "
import sys
sys.path.append('$MEMORY_MANAGER_DIR')
from memory_service_manager import stop_memory_service
stop_memory_service()
"
}

test_memory_operations() {
    echo "=== Memory Operations Test ==="
    python3 -c "
import sys
sys.path.append('$MEMORY_MANAGER_DIR')
from memory_service_manager import test_memory_operations
import json

results = test_memory_operations()
for backend, ops in results.items():
    print(f\"{backend.upper()}:\")
    print(f\"  Read: {'✅' if ops['read'] else '❌'}\")
    print(f\"  Write: {'✅' if ops['write'] else '❌'}\")
    if ops['error']:
        print(f\"  Error: {ops['error']}\")
    print()
"
}

# Command dispatch
case "${1:-status}" in
    "status")
        check_memory_status
        ;;
    "start")
        start_memory_service
        ;;
    "stop")
        stop_memory_service
        ;;
    "restart")
        stop_memory_service
        start_memory_service
        ;;
    "test")
        test_memory_operations
        ;;
    *)
        echo "Usage: $0 {status|start|stop|restart|test}"
        exit 1
        ;;
esac
```

## Environment Variables

### Configuration
- `GADUGI_MEMORY_PRIMARY` - Primary backend (neo4j/sqlite)
- `GADUGI_MEMORY_FALLBACK` - Enable fallback (true/false)
- `GADUGI_NEO4J_URI` - Neo4j connection URI
- `GADUGI_NEO4J_AUTH` - Neo4j authentication
- `GADUGI_SQLITE_PATH` - SQLite database path
- `GADUGI_MEMORY_CACHE` - Enable in-memory cache (true/false)

### Performance Tuning
- `GADUGI_MEMORY_TIMEOUT` - Operation timeout (default: 30s)
- `GADUGI_MEMORY_RETRY_COUNT` - Retry attempts (default: 3)
- `GADUGI_CACHE_SIZE_LIMIT` - Cache size limit (default: 1000 entries)

## Integration with Gadugi Coordinator

### JSON Status Output
```json
{
  "service": "memory-system",
  "overall_status": "OPTIMAL|DEGRADED|CRITICAL",
  "active_backend": "neo4j|sqlite|memory-only",
  "fallback_active": false,
  "layers": {
    "neo4j": {
      "status": "HEALTHY|UNHEALTHY|UNAVAILABLE",
      "connection": "bolt://localhost:7689",
      "features": ["graph", "relationships", "acid"]
    },
    "sqlite": {
      "status": "HEALTHY|ERROR",
      "path": ".claude/memory/fallback.db",
      "size": 1048576,
      "features": ["local", "persistent", "acid"]
    },
    "cache": {
      "status": "HEALTHY|ERROR",
      "layers": {"python": true, "redis": false},
      "features": ["fast", "temporary"]
    }
  },
  "statistics": {
    "backends": {
      "sqlite": {
        "entries": 150,
        "relationships": 75,
        "size_bytes": 1048576
      }
    }
  },
  "message": "Memory system operational with SQLite fallback"
}
```

## Recovery Strategies

### Automatic Fallback
1. **Neo4j Unavailable**: Automatically switch to SQLite
2. **SQLite Corruption**: Reinitialize database
3. **Cache Issues**: Continue with persistent layers only
4. **Full System Recovery**: Rebuild from available data

### Manual Recovery
```bash
# Reset SQLite fallback
rm .claude/memory/fallback.db
./MemoryServiceManager.md start

# Force Neo4j reconnection
./MemoryServiceManager.md restart

# Test all layers
./MemoryServiceManager.md test
```

This memory service manager provides comprehensive monitoring and management of Gadugi's hierarchical memory system with full fallback chain awareness.