#!/usr/bin/env python3
import httpx
import json
import asyncio
from datetime import datetime


async def test_proxy():
    """Test the proxy with a valid request that should be logged."""
    url = "http://localhost:8082/v1/messages"

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": "test-key",  # Any key since validation is disabled
    }

    payload = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": "TEST_REQUEST: What is 2+2? This request should appear in logs.",
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7,
    }

    print(f"[{datetime.now().isoformat()}] Sending test request to {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print(
                f"[{datetime.now().isoformat()}] Response status: {response.status_code}"
            )
            print(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                # Try to read streaming response
                content = ""
                async for chunk in response.aiter_text():
                    content += chunk
                    print(f"Chunk received: {chunk[:100]}...")
                print(f"Full response: {content[:500]}...")
            else:
                print(f"Response body: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_proxy())
