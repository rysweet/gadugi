#!/usr/bin/env python3
"""Direct test of Azure OpenAI endpoint to diagnose issues."""

import os
import httpx
from pathlib import Path

# Load configuration
config_file = Path(__file__).parent / ".env"
config = {}
if config_file.exists():
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                config[key] = value

print("Configuration loaded:")
print(f"  Endpoint: {config.get('AZURE_OPENAI_ENDPOINT')}")
print(f"  Deployment: {config.get('AZURE_OPENAI_DEPLOYMENT_NAME')}")
print(f"  API Version: {config.get('AZURE_API_VERSION')}")
print()

# Test different API versions
api_versions = [
    "2025-01-01-preview",
    "2024-10-01-preview", 
    "2024-08-01-preview",
    "2024-06-01",
    "2024-02-15-preview",
    "2024-02-01",
    "2023-12-01-preview",
    "2023-05-15"
]

base_url = config.get('AZURE_OPENAI_ENDPOINT')
deployment = config.get('AZURE_OPENAI_DEPLOYMENT_NAME')
api_key = config.get('AZURE_OPENAI_API_KEY')

print("Testing Azure OpenAI endpoint with different API versions...")
print("=" * 60)

for version in api_versions:
    url = f"{base_url}/openai/deployments/{deployment}/chat/completions?api-version={version}"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 1
    }
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {version}: SUCCESS")
            print(f"   Valid API version found!")
            break
        elif response.status_code == 404:
            print(f"❌ {version}: 404 Not Found")
        elif response.status_code == 401:
            print(f"❌ {version}: 401 Unauthorized")
        elif response.status_code == 400:
            error_detail = response.json().get('error', {}).get('message', 'Unknown')
            print(f"⚠️  {version}: 400 Bad Request - {error_detail}")
        else:
            print(f"❓ {version}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ {version}: Error - {str(e)}")

print("\n" + "=" * 60)
print("\nTesting deployment list endpoint...")

# Try to list deployments
list_url = f"{base_url}/openai/deployments?api-version=2024-02-01"
try:
    response = httpx.get(list_url, headers={"api-key": api_key}, timeout=10)  # type: ignore[assignment]
    if response.status_code == 200:
        data = response.json()
        print("✅ Available deployments:")
        for deployment in data.get('data', []):
            print(f"   - {deployment.get('id')} (model: {deployment.get('model')})")
    else:
        print(f"❌ Cannot list deployments: {response.status_code}")
except Exception as e:
    print(f"❌ Error listing deployments: {e}")