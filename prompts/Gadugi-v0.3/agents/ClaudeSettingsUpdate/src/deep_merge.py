import json
from collections import OrderedDict

# Read both settings files
with open('.claude/settings.json', 'r') as f:
    global_settings = json.load(f)

with open('.claude/settings.local.json', 'r') as f:
    local_settings = json.load(f)

def deep_merge(global_dict, local_dict):
    """Deep merge with local taking precedence"""
    result = global_dict.copy()

    for key, value in local_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key == 'allow' and isinstance(value, list):
            # Special handling for allow-list: merge and deduplicate
            existing = result.get(key, [])
            combined = list(OrderedDict.fromkeys(existing + value))
            result[key] = sorted(combined)
        else:
            result[key] = value

    return result

# Merge settings
merged_settings = deep_merge(global_settings, local_settings)
