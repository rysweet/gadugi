# Implement Non-Disruptive Gadugi Installation System

## Objective
Implement a non-disruptive installation system for Gadugi that keeps all artifacts within `.claude/` and `.github/` directories, based on the reviewed design with risk mitigations.

## Background
Based on PM review, we're implementing a GitHub-based installer (not custom domain) with robust fallbacks and focusing on reliability over features.

## Key Requirements
1. **Complete Isolation**: ALL Gadugi files must go in `.claude/` directory (except `.github/Memory.md`)
2. **One-Line Install**: `curl -fsSL https://raw.githubusercontent.com/rysweet/gadugi/main/install.sh | sh`
3. **Automatic Dependencies**: Handle UV, Python packages, all setup automatically
4. **Clean Uninstall**: Complete removal with no traces left behind
5. **Robust Fallbacks**: Multiple installation methods for reliability

## Implementation Tasks

### Phase 1: Core Installation Script
Create `/install.sh` in repository root with:
- Platform detection (macOS, Linux, Windows-WSL)
- Directory structure creation in `.claude/`
- UV installation with fallbacks (curl → pip → manual binary)
- Python virtual environment setup in `.claude/venv/`
- Error handling and logging

### Phase 2: Agent Bootstrap System
Create `.claude/scripts/bootstrap-agents.sh`:
- Download core agents first (orchestrator-agent, workflow-manager, code-reviewer)
- Parallel download with progress indicators
- Checksum verification
- Agent validation tests
- Graceful degradation if non-essential agents fail

### Phase 3: Configuration Management
Create `.claude/config/gadugi.yaml`:
- Dynamic configuration based on detected environment
- Agent registry with versions
- Installation metadata
- Update tracking

### Phase 4: Uninstall Script
Create `.claude/scripts/uninstall.sh`:
- Remove `.claude/` directory completely
- Remove `.github/Memory.md` if Gadugi-managed
- Clean git config entries
- Confirmation prompts

### Phase 5: README Updates
Update `README.md`:
- Move current Prerequisites and Setup to "Development" section
- Create new "Installation" section with one-liner
- Update Bootstrap Agent Manager section
- Add troubleshooting guide

## Directory Structure to Create
```
.claude/
├── agents/                 # All agent definitions
├── venv/                   # Python virtual environment
├── scripts/
│   ├── bootstrap-agents.sh # Agent installation
│   ├── health-check.sh    # System validation
│   ├── repair.sh          # Fix broken installations
│   └── uninstall.sh       # Clean removal
├── config/
│   └── gadugi.yaml        # Configuration
├── cache/                 # Download cache
├── logs/                  # Installation logs
└── templates/             # Prompt templates
```

## Success Criteria
1. Installation completes in < 5 minutes on standard connection
2. No files created outside `.claude/` and `.github/` directories
3. Core agents (3) operational immediately after install
4. Clean uninstall leaves no traces
5. Works on macOS, Linux, and Windows-WSL

## Testing Requirements
1. Test in clean repository with no prior Gadugi installation
2. Test with existing `.claude/` directory from other tools
3. Test offline/air-gapped fallback modes
4. Test uninstall and reinstall cycle
5. Verify no pollution of user's repository

## Deliverables
1. `/install.sh` - Main installation script
2. `.claude/scripts/` - All supporting scripts
3. Updated `README.md` with new installation instructions
4. Test results documenting clean installation
5. Issue and PR for tracking this work

## Priority Order
1. Basic install.sh that creates directories and installs UV
2. Agent bootstrap for core 3 agents
3. Configuration and validation
4. Uninstall capability
5. README updates

Focus on reliability and robustness over features. Start with minimal viable installation and build from there.
