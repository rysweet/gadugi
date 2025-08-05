#!/bin/bash
# XPIA Web Hooks Setup Script
# Configures Claude Code to use XPIA defense for web operations only

set -e

echo "=== XPIA Web Operations Hook Setup ==="
echo
echo "This will configure XPIA defense for WebFetch and WebSearch operations only."
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Claude Code settings exist
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

if [ ! -f "$CLAUDE_SETTINGS" ]; then
    echo "Creating Claude Code settings file at: $CLAUDE_SETTINGS"
    mkdir -p "$HOME/.claude"
    echo '{}' > "$CLAUDE_SETTINGS"
fi

# Create backup
BACKUP_FILE="$CLAUDE_SETTINGS.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CLAUDE_SETTINGS" "$BACKUP_FILE"
echo "Backed up current settings to: $BACKUP_FILE"

# Read existing settings
if command -v jq &> /dev/null; then
    # If jq is available, merge settings properly
    EXISTING_SETTINGS=$(cat "$CLAUDE_SETTINGS")
    NEW_HOOKS=$(cat << EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      },
      {
        "matcher": "WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      },
      {
        "matcher": "WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      }
    ]
  }
}
EOF
)
    echo "$EXISTING_SETTINGS" | jq ". + $NEW_HOOKS" > "$CLAUDE_SETTINGS.xpia_temp"
else
    # Without jq, create new settings file
    cat > "$CLAUDE_SETTINGS.xpia_temp" << EOF
{
  "\$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "opus",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      },
      {
        "matcher": "WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      },
      {
        "matcher": "WebSearch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $SCRIPT_DIR/xpia_web_validator.py"
          }
        ]
      }
    ]
  }
}
EOF
fi

echo
echo "Preview of settings with XPIA web hooks:"
echo "----------------------------------------"
cat "$CLAUDE_SETTINGS.xpia_temp" | python3 -m json.tool 2>/dev/null || cat "$CLAUDE_SETTINGS.xpia_temp"
echo "----------------------------------------"
echo

read -p "Apply these settings? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mv "$CLAUDE_SETTINGS.xpia_temp" "$CLAUDE_SETTINGS"
    echo "✅ XPIA web hooks configured successfully!"
    echo
    echo "The following operations are now protected:"
    echo "  - WebFetch: URLs and prompts validated before fetching"
    echo "  - WebSearch: Search queries validated before execution"
    echo "  - Web content: Returned content sanitized for safety"
    echo
    echo "To test: Try using WebFetch with a malicious prompt"
    echo "To disable: Restore settings from $BACKUP_FILE"
else
    rm "$CLAUDE_SETTINGS.xpia_temp"
    echo "Setup cancelled. No changes made."
fi
