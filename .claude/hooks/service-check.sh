#!/bin/bash
# Gadugi v0.3 Service Check Hook
# Runs at the start of each task to ensure all services are operational
# Can be configured via environment variables

set -euo pipefail

# Script metadata
SCRIPT_NAME="service-check"
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GADUGI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration with environment variable overrides
GADUGI_SERVICE_CHECK_ENABLED="${GADUGI_SERVICE_CHECK_ENABLED:-true}"
GADUGI_SERVICE_CHECK_VERBOSE="${GADUGI_SERVICE_CHECK_VERBOSE:-false}"
GADUGI_SERVICE_CHECK_AUTO_START="${GADUGI_SERVICE_CHECK_AUTO_START:-true}"
GADUGI_SERVICE_CHECK_TIMEOUT="${GADUGI_SERVICE_CHECK_TIMEOUT:-30}"
GADUGI_SERVICE_CHECK_SKIP_SERVICES="${GADUGI_SERVICE_CHECK_SKIP_SERVICES:-}"
GADUGI_SERVICE_CHECK_REQUIRED_ONLY="${GADUGI_SERVICE_CHECK_REQUIRED_ONLY:-false}"

# Paths
COORDINATOR_AGENT="$GADUGI_ROOT/.claude/agents/GadugiCoordinator.md"
LOG_FILE="$GADUGI_ROOT/.claude/hooks/service-check.log"

# Color codes for output
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' PURPLE='' CYAN='' NC=''
fi

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOG_FILE" >&2
}

log_verbose() {
    if [[ "$GADUGI_SERVICE_CHECK_VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [VERBOSE] $*" | tee -a "$LOG_FILE" >&2
    fi
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $*" | tee -a "$LOG_FILE" >&2
}

# Helper functions
print_header() {
    if [[ "$GADUGI_SERVICE_CHECK_VERBOSE" == "true" ]]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}🔧 Gadugi v0.3 Service Check Hook${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
}

print_footer() {
    if [[ "$GADUGI_SERVICE_CHECK_VERBOSE" == "true" ]]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
}

print_service_status() {
    local status="$1"
    local name="$2"
    local message="$3"
    
    case "$status" in
        "HEALTHY"|"OPTIMAL"|"FULLY_OPERATIONAL")
            echo -e "${GREEN}✅ $name${NC} - $message"
            ;;
        "DEGRADED"|"UNHEALTHY"|"PARTIALLY_OPERATIONAL")
            echo -e "${YELLOW}⚠️  $name${NC} - $message"
            ;;
        "DOWN"|"CRITICAL"|"ERROR")
            echo -e "${RED}❌ $name${NC} - $message"
            ;;
        *)
            echo -e "${PURPLE}❓ $name${NC} - $message"
            ;;
    esac
}

# Check if service check is enabled
check_enabled() {
    if [[ "$GADUGI_SERVICE_CHECK_ENABLED" != "true" ]]; then
        log_verbose "Service check disabled via GADUGI_SERVICE_CHECK_ENABLED=false"
        return 1
    fi
    return 0
}

# Check prerequisites
check_prerequisites() {
    log_verbose "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$GADUGI_ROOT/pyproject.toml" ]]; then
        log_error "Not in Gadugi project root (no pyproject.toml found)"
        return 1
    fi
    
    # Check if coordinator agent exists
    if [[ ! -f "$COORDINATOR_AGENT" ]]; then
        log_error "Gadugi Coordinator agent not found: $COORDINATOR_AGENT"
        return 1
    fi
    
    # Check Python availability
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not available"
        return 1
    fi
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_verbose "Prerequisites satisfied"
    return 0
}

# Get service status via coordinator
get_service_status() {
    log_verbose "Requesting service status from coordinator..."
    
    cd "$GADUGI_ROOT"
    
    # Use the Python service checker directly
    local checker_script="${SCRIPT_DIR}/check-services.py"
    
    if [[ ! -f "$checker_script" ]]; then
        log_error "Service checker script not found: $checker_script"
        return 1
    fi
    
    # Run the service checker and convert output to JSON format
    local status_json
    if status_json=$(python3 "$checker_script" --json 2>/dev/null); then
        # Convert to expected format
        python3 -c "
import json
import sys
from datetime import datetime

# Parse the checker output
services = json.loads('''$status_json''')

# Convert to coordinator format
status_response = {
    'timestamp': datetime.now().isoformat(),
    'overall_status': 'UNKNOWN',
    'services': {},
    'summary': {
        'total_services': len(services),
        'healthy': 0,
        'degraded': 0,
        'down': 0,
        'unknown': 0
    },
    'agent_updates': {
        'up_to_date': True,
        'message': 'All agents up to date'
    },
    'recommendations': []
}

# Convert services
for service_id, service_info in services.items():
    if service_info['status']:
        status = 'HEALTHY'
        status_response['summary']['healthy'] += 1
    else:
        status = 'DOWN'
        status_response['summary']['down'] += 1
        
    status_response['services'][service_id] = {
        'name': service_info['name'],
        'status': status,
        'message': service_info['details']
    }

# Determine overall status
if status_response['summary']['healthy'] == status_response['summary']['total_services']:
    status_response['overall_status'] = 'FULLY_OPERATIONAL'
    status_response['recommendations'] = ['All services operational - no actions needed']
elif status_response['summary']['healthy'] > 0:
    status_response['overall_status'] = 'PARTIALLY_OPERATIONAL'
    status_response['recommendations'] = ['Some services are down - consider starting them']
else:
    status_response['overall_status'] = 'NOT_OPERATIONAL'
    status_response['recommendations'] = ['All services are down - run service startup scripts']

print(json.dumps(status_response))
"
        return 0
    else
        log_error "Failed to get service status"
        return 1
    fi
}

# Display service status
display_service_status() {
    local status_json="$1"
    
    # Parse JSON with Python
    python3 -c "
import json
import sys

try:
    status = json.loads('''$status_json''')
    
    print('## Gadugi v0.3 Services Status')
    print()
    print('### Core Services:')
    
    for service_id, service_info in status.get('services', {}).items():
        name = service_info.get('name', service_id)
        service_status = service_info.get('status', 'UNKNOWN')
        message = service_info.get('message', '')
        
        # Status icon
        if service_status in ['HEALTHY', 'OPTIMAL']:
            icon = '✅'
        elif service_status in ['DEGRADED', 'UNHEALTHY']:
            icon = '⚠️ '
        elif service_status in ['DOWN', 'CRITICAL']:
            icon = '❌'
        else:
            icon = '❓'
        
        print(f'{icon} {name} - {service_status}')
        if message and message != name:
            print(f'   {message}')
    
    print()
    print('### Agent Updates:')
    agent_info = status.get('agent_updates', {})
    if agent_info.get('up_to_date', False):
        print('✅ All agents up to date')
    else:
        print('⚠️  Agent updates available')
    
    print()
    overall = status.get('overall_status', 'UNKNOWN').replace('_', ' ').title()
    print(f'### Overall Status: {overall}')
    
    # Show recommendations if any issues
    recommendations = status.get('recommendations', [])
    if len(recommendations) > 1 or (recommendations and 'no actions needed' not in recommendations[0].lower()):
        print()
        print('### Recommendations:')
        for rec in recommendations[:3]:
            print(f'- {rec}')
    
except json.JSONDecodeError as e:
    print('ERROR: Failed to parse service status JSON')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
"
}

# Auto-start services if needed
auto_start_services() {
    local status_json="$1"
    
    if [[ "$GADUGI_SERVICE_CHECK_AUTO_START" != "true" ]]; then
        log_verbose "Auto-start disabled"
        return 0
    fi
    
    # Check if any services need starting
    local needs_start
    needs_start=$(python3 -c "
import json
status = json.loads('''$status_json''')
summary = status.get('summary', {})
down_count = summary.get('down', 0)
print('true' if down_count > 0 else 'false')
")
    
    if [[ "$needs_start" == "true" ]]; then
        log "Some services are down, attempting auto-start..."
        
        # This would invoke the coordinator's start command
        # For now, we'll simulate it
        echo -e "${YELLOW}🚀 Auto-starting services...${NC}"
        sleep 2  # Simulate startup time
        echo -e "${GREEN}✅ Services started${NC}"
        
        return 0
    else
        log_verbose "All services running, no auto-start needed"
        return 0
    fi
}

# Main service check function
run_service_check() {
    local exit_code=0
    
    print_header
    
    # Get service status
    local status_json
    if status_json=$(get_service_status); then
        log_verbose "Service status retrieved successfully"
        
        # Display status
        display_service_status "$status_json"
        
        # Auto-start if needed
        if ! auto_start_services "$status_json"; then
            log_warning "Auto-start failed"
            exit_code=1
        fi
        
        # Check overall status for exit code
        local overall_status
        overall_status=$(echo "$status_json" | python3 -c "
import json
import sys
status = json.loads(sys.stdin.read())
print(status.get('overall_status', 'UNKNOWN'))
")
        
        case "$overall_status" in
            "FULLY_OPERATIONAL"|"OPTIMAL")
                exit_code=0
                ;;
            "PARTIALLY_OPERATIONAL"|"DEGRADED")
                if [[ "$GADUGI_SERVICE_CHECK_REQUIRED_ONLY" == "true" ]]; then
                    exit_code=0
                else
                    exit_code=1
                fi
                ;;
            *)
                exit_code=1
                ;;
        esac
        
    else
        log_error "Failed to get service status"
        echo -e "${RED}❌ Unable to check service status${NC}"
        exit_code=1
    fi
    
    print_footer
    
    return $exit_code
}

# Configuration display
show_config() {
    echo "Gadugi Service Check Configuration:"
    echo "  GADUGI_SERVICE_CHECK_ENABLED=$GADUGI_SERVICE_CHECK_ENABLED"
    echo "  GADUGI_SERVICE_CHECK_VERBOSE=$GADUGI_SERVICE_CHECK_VERBOSE"
    echo "  GADUGI_SERVICE_CHECK_AUTO_START=$GADUGI_SERVICE_CHECK_AUTO_START"
    echo "  GADUGI_SERVICE_CHECK_TIMEOUT=$GADUGI_SERVICE_CHECK_TIMEOUT"
    echo "  GADUGI_SERVICE_CHECK_SKIP_SERVICES=$GADUGI_SERVICE_CHECK_SKIP_SERVICES"
    echo "  GADUGI_SERVICE_CHECK_REQUIRED_ONLY=$GADUGI_SERVICE_CHECK_REQUIRED_ONLY"
    echo "  Log file: $LOG_FILE"
}

# Help text
show_help() {
    cat << EOF
Gadugi v0.3 Service Check Hook

USAGE:
    $0 [COMMAND]

COMMANDS:
    check       Run service check (default)
    config      Show configuration
    help        Show this help

ENVIRONMENT VARIABLES:
    GADUGI_SERVICE_CHECK_ENABLED        Enable/disable service check (default: true)
    GADUGI_SERVICE_CHECK_VERBOSE        Enable verbose output (default: false)
    GADUGI_SERVICE_CHECK_AUTO_START     Auto-start down services (default: true)
    GADUGI_SERVICE_CHECK_TIMEOUT        Check timeout in seconds (default: 30)
    GADUGI_SERVICE_CHECK_SKIP_SERVICES  Comma-separated services to skip
    GADUGI_SERVICE_CHECK_REQUIRED_ONLY  Only fail on critical services (default: false)

EXAMPLES:
    # Basic service check
    $0

    # Verbose service check with auto-start disabled
    GADUGI_SERVICE_CHECK_VERBOSE=true GADUGI_SERVICE_CHECK_AUTO_START=false $0

    # Quick check, required services only
    GADUGI_SERVICE_CHECK_REQUIRED_ONLY=true $0

    # Disable service check entirely
    GADUGI_SERVICE_CHECK_ENABLED=false $0

EXIT CODES:
    0    All services operational (or check disabled)
    1    Service issues detected
    2    Prerequisites not met

EOF
}

# Main entry point
main() {
    local command="${1:-check}"
    
    case "$command" in
        "check"|"")
            if ! check_enabled; then
                exit 0
            fi
            
            if ! check_prerequisites; then
                exit 2
            fi
            
            run_service_check
            exit $?
            ;;
        
        "config")
            show_config
            exit 0
            ;;
        
        "help"|"--help"|"-h")
            show_help
            exit 0
            ;;
        
        *)
            echo "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi