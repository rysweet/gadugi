import json

# Compare with existing settings
try:
    with open('.claude/settings.json', 'r') as f:
        current_settings = json.load(f)

    if merged_settings == current_settings:
        print("No changes detected - skipping PR creation")
        exit(0)

except Exception as e:
    print(f"Error reading current settings: {e}")
