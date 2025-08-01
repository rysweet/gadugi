#!/bin/bash
# setup-hooks.sh - Configure agent-manager startup hooks in Claude Code settings

set -euo pipefail

# Ensure .gitignore is properly configured
ensure_gitignore() {
    echo "📋 Ensuring .gitignore is properly configured..."
    
    local gitignore_file=".gitignore"
    local entries_to_add=(
        "# Claude Code agent-manager"
        ".claude/agent-manager/cache/last-check-timestamp"
        ".claude/agent-manager/logs/"
        ".claude/agent-manager/tests/__pycache__/"
        ".claude/cache/"
        ".claude/hooks/"
        ".claude/logs/"
        ""
        "# Agent-manager runtime files"
        ".claude/agent-manager/hooks/check-agent-updates.sh"
    )
    
    # Create .gitignore if it doesn't exist
    if [ ! -f "$gitignore_file" ]; then
        echo "📄 Creating new .gitignore file..."
        touch "$gitignore_file"
    fi
    
    # Check and add each entry if not present
    local added=0
    for entry in "${entries_to_add[@]}"; do
        if [ -n "$entry" ] && ! grep -Fxq "$entry" "$gitignore_file"; then
            echo "$entry" >> "$gitignore_file"
            ((added++))
        fi
    done
    
    if [ $added -gt 0 ]; then
        echo "✅ Added $added entries to .gitignore"
    else
        echo "✅ .gitignore already properly configured"
    fi
}

# Main setup function
setup_startup_hooks() {
    echo "🔗 Setting up Agent Manager startup hooks..."
    
    local settings_file=".claude/settings.json"
    local backup_file=".claude/settings.json.backup.$(date +%s)"
    local hooks_dir=".claude/hooks"
    local script_source=".claude/agent-manager/hooks/check-agent-updates.sh"
    local script_target="$hooks_dir/check-agent-updates.sh"
    
    # Create hooks directory if it doesn't exist
    mkdir -p "$hooks_dir"
    
    # Install the check-agent-updates.sh script to .claude/hooks/
    echo "📦 Installing agent update checker script..."
    
    if [ -f "$script_source" ]; then
        echo "📄 Copying script from $script_source to $script_target"
        cp "$script_source" "$script_target"
        chmod +x "$script_target"
        echo "✅ Script installed and made executable"
    else
        echo "⚠️  Source script not found at $script_source"
        echo "🔧 Creating script at target location..."
        
        # Create the script directly if source doesn't exist
        cat > "$script_target" << 'SCRIPT_EOF'
#!/bin/sh
# check-agent-updates.sh - Lightweight agent update checker
echo "🚀 Claude Code session started"
echo "🤖 Agent Manager available"
echo "💡 Use '/agent:agent-manager check-and-update-agents' to check for updates"
SCRIPT_EOF
        chmod +x "$script_target"
        echo "✅ Basic script created and made executable"
    fi
    
    # Create backup if settings.json exists
    if [ -f "$settings_file" ]; then
        echo "💾 Creating backup of existing settings.json..."
        cp "$settings_file" "$backup_file"
    fi
    
    # Create default settings if file doesn't exist
    if [ ! -f "$settings_file" ]; then
        echo "📄 Creating new settings.json file..."
        mkdir -p ".claude"
        echo "{}" > "$settings_file"
    fi
    
    # Read existing settings
    local existing_settings
    if ! existing_settings=$(cat "$settings_file" 2>/dev/null); then
        echo "⚠️  Failed to read existing settings, creating new file..."
        echo "{}" > "$settings_file"
        existing_settings="{}"
    fi
    
    # Validate JSON syntax
    if ! echo "$existing_settings" | python3 -m json.tool >/dev/null 2>&1; then
        echo "⚠️  Invalid JSON in settings.json, creating backup and recreating..."
        cp "$settings_file" "$backup_file.invalid"
        existing_settings="{}"
        # Write valid empty JSON to the file
        echo "{}" > "$settings_file"
    fi
    
    # Create agent-manager hook configuration
    # This hook executes the shell script instead of trying to invoke Claude agents
    local agent_manager_hook=$(cat << 'EOH'
{
  "matchers": {
    "sessionType": ["startup", "resume"]
  },
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/check-agent-updates.sh --quiet"
    }
  ]
}
EOH
)
    
    # Use Python to merge JSON preserving existing settings
    python3 << PYTHON_SCRIPT
import json
import sys

try:
    # Read existing settings
    with open('$settings_file', 'r') as f:
        settings = json.load(f)
    
    # Ensure hooks section exists
    if 'hooks' not in settings:
        settings['hooks'] = {}
    
    # Ensure SessionStart section exists
    if 'SessionStart' not in settings['hooks']:
        settings['hooks']['SessionStart'] = []
    
    # Create agent-manager hook
    agent_manager_hook = $agent_manager_hook
    
    # Check if agent-manager hook already exists and remove it
    # Remove hooks that contain check-agent-updates.sh or old agent-manager syntax
    settings['hooks']['SessionStart'] = [
        hook for hook in settings['hooks']['SessionStart'] 
        if not (isinstance(hook.get('hooks'), list) and 
                any('check-agent-updates.sh' in h.get('command', '') or
                    'agent-manager' in h.get('command', '') 
                    for h in hook.get('hooks', []))) and
        not (isinstance(hook.get('command'), str) and 
             ('check-agent-updates.sh' in hook.get('command', '') or
              'agent-manager' in hook.get('command', '')))
    ]
    
    # Add the new agent-manager hook
    settings['hooks']['SessionStart'].append(agent_manager_hook)
    
    # Write updated settings
    with open('$settings_file', 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("✅ Successfully updated settings.json with agent-manager hooks")
    
except Exception as e:
    print(f"❌ Error updating settings.json: {e}")
    sys.exit(1)
PYTHON_SCRIPT
    
    local python_exit_code=$?
    
    if [ $python_exit_code -ne 0 ]; then
        echo "❌ Failed to update settings.json with Python"
        
        # Fallback: restore backup if it exists
        if [ -f "$backup_file" ]; then
            echo "🔄 Restoring backup..."
            cp "$backup_file" "$settings_file"
        fi
        
        return 1
    fi
    
    # Validate the final JSON
    if ! python3 -m json.tool "$settings_file" >/dev/null 2>&1; then
        echo "❌ Generated invalid JSON, restoring backup..."
        if [ -f "$backup_file" ]; then
            cp "$backup_file" "$settings_file"
        fi
        return 1
    fi
    
    echo "✅ Startup hooks configured in $settings_file"
    echo "💡 Backup created at: $backup_file"
    
    # Ensure .gitignore is properly configured
    ensure_gitignore
    
    # Show the hooks section for verification
    echo "📋 Current SessionStart hooks:"
    python3 -c "
import json
try:
    with open('$settings_file', 'r') as f:
        settings = json.load(f)
    hooks = settings.get('hooks', {}).get('SessionStart', [])
    if hooks:
        for i, hook in enumerate(hooks):
            print(f'  {i+1}. {hook}')
    else:
        print('  No SessionStart hooks found')
except Exception as e:
    print(f'  Error reading hooks: {e}')
"
}

# Execute if run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    setup_startup_hooks
fi