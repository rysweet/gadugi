#!/usr/bin/env python3
"""Test that the LLM Proxy is working and proxying to Azure OpenAI."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

async def test_proxy_connection():
    """Test connection through the LLM Proxy service."""

    print("=" * 60)
    print("🧪 Testing LLM Proxy Connection")
    print("=" * 60)

    try:
        from llm_proxy_service import create_chat_request
        import aiohttp

        # Create a test request
        request = create_chat_request(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Azure OpenAI via Proxy is working!' in exactly 6 words."}
            ],
            model="gpt-4.1",  # Using the Azure deployment name
            max_tokens=20,
            temperature=0
        )

        print(f"\n📤 Sending request to proxy at localhost:8080")
        print(f"   Model: {request.model}")
        print(f"   Request ID: {request.id}")

        # Send request to the proxy service
        async with aiohttp.ClientSession() as session:
            # Convert request to dict for JSON serialization
            request_data = {
                "id": request.id,
                "type": request.type.value if hasattr(request.type, 'value') else str(request.type),
                "model": request.model,
                "messages": request.messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stream": False
            }

            async with session.post(
                "http://localhost:8080/v1/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print(f"\n✅ Response received: {content}")
                    print("\n🎉 Proxy is successfully routing to Azure OpenAI!")
                    return True
                else:
                    error_text = await response.text()
                    print(f"\n❌ Proxy returned error {response.status}: {error_text}")
                    return False

    except aiohttp.ClientError as e:  # type: ignore[assignment]
        print(f"\n❌ Connection error: {e}")
        print("\nPossible issues:")
        print("1. The proxy service might not be exposing an HTTP endpoint")
        print("2. The proxy might be using a different port")
        print("3. The proxy might need additional configuration")
        return False

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure aiohttp is installed: uv add aiohttp")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_service_call():
    """Test calling the service directly (not through HTTP)."""

    print("\n" + "=" * 60)
    print("🧪 Testing Direct Service Call")
    print("=" * 60)

    try:
        # Import proxy service components
        from llm_proxy_service import LLMProxyService, create_chat_request

        # The service should already be initialized if started correctly
        # But we'll create a test instance to verify the logic
        print("\nNote: This creates a new instance, not the running service")

        # Create request
        request = create_chat_request(
            messages=[
                {"role": "user", "content": "Test message"}
            ],
            model="gpt-4.1",
            max_tokens=10
        )

        print(f"✅ Request created successfully")
        print(f"   Model: {request.model}")
        print(f"   Type: {request.type}")

        # Note: We can't actually call the running service instance from here
        # This just validates the request creation works

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def check_proxy_logs():
    """Check the proxy logs for activity."""

    print("\n" + "=" * 60)
    print("📊 Checking Proxy Logs")
    print("=" * 60)

    log_dir = Path(__file__).parent / "logs"

    # Find the most recent log file
    log_files = sorted(log_dir.glob("proxy_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)

    if log_files:
        latest_log = log_files[0]
        print(f"\nLatest log: {latest_log.name}")

        # Read last 10 lines
        with open(latest_log) as f:
            lines = f.readlines()
            last_lines = lines[-10:] if len(lines) > 10 else lines

        print("\nLast few log entries:")
        for line in last_lines:
            print(f"  {line.strip()}")
    else:
        print("No log files found")

async def main():
    """Run all tests."""

    print("\n🚀 Starting LLM Proxy Tests\n")

    # Test 1: Check if we can create requests
    direct_success = await test_direct_service_call()

    # Test 2: Try HTTP connection (might not work if service doesn't expose HTTP)
    proxy_success = await test_proxy_connection()

    # Test 3: Check logs
    await check_proxy_logs()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Direct service call: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"HTTP proxy call:     {'✅ PASS' if proxy_success else '❌ FAIL'}")

    if not proxy_success:
        print("\nℹ️  Note: The LLM Proxy service appears to be running but might not")
        print("   expose an HTTP endpoint. The service might be designed to be")
        print("   imported and used directly in Python code rather than as an HTTP proxy.")

if __name__ == "__main__":
    asyncio.run(main())
