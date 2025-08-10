"""
GitHub API client for Gadugi Event Service

Handles GitHub API interactions for polling and webhook management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class GitHubClient:
    """Async GitHub API client for the Gadugi Event Service."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client."""
        self.token = token
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()

        if not self.token:
            logger.warning("No GitHub token provided - API requests will be limited")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Gadugi-Event-Service/0.1.0",
            }

            if self.token:
                headers["Authorization"] = f"token {self.token}"

            self.session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to GitHub API."""
        await self._ensure_session()

        url = urljoin(self.base_url, endpoint)

        # Check rate limiting
        if self.rate_limit_remaining <= 10 and datetime.now() < self.rate_limit_reset:
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            logger.warning(f"Rate limit approaching, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)

        try:
            async with self.session.request(method, url, **kwargs) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get("X-RateLimit-Remaining", 0)
                )
                reset_timestamp = int(response.headers.get("X-RateLimit-Reset", 0))
                if reset_timestamp:
                    self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)

                if response.status == 404:
                    logger.warning(f"GitHub API 404: {endpoint}")
                    return {}

                response.raise_for_status()

                # Handle different content types
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                else:
                    text = await response.text()
                    return {"content": text}

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API request failed: {e}")
            raise

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        return await self._request("GET", f"/repos/{owner}/{repo}")

    async def get_events_since(
        self, since: datetime, owner: str = None, repo: str = None
    ) -> List[Dict[str, Any]]:
        """Get events since the specified time."""
        if owner and repo:
            # Repository-specific events
            endpoint = f"/repos/{owner}/{repo}/events"
        else:
            # User events (requires authentication)
            if not self.token:
                logger.warning("Cannot fetch user events without authentication")
                return []
            endpoint = "/events"

        try:
            events = await self._request("GET", endpoint)
            if not isinstance(events, list):
                return []

            # Filter events by time
            since_str = since.isoformat() + "Z"
            filtered_events = []

            for event in events:
                event_time = event.get("created_at", "")
                if event_time and event_time >= since_str:
                    filtered_events.append(event)

            logger.debug(f"Found {len(filtered_events)} events since {since}")
            return filtered_events

        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get repository issues."""
        params = {"state": state}
        if since:
            params["since"] = since.isoformat() + "Z"

        try:
            return await self._request(
                "GET", f"/repos/{owner}/{repo}/issues", params=params
            )
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            return []

    async def get_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """Get repository pull requests."""
        params = {"state": state}

        try:
            return await self._request(
                "GET", f"/repos/{owner}/{repo}/pulls", params=params
            )
        except Exception as e:
            logger.error(f"Error fetching pull requests: {e}")
            return []

    async def create_webhook(
        self,
        owner: str,
        repo: str,
        webhook_url: str,
        secret: str,
        events: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a webhook for the repository."""
        if not self.token:
            raise ValueError("GitHub token required for webhook creation")

        if events is None:
            events = ["issues", "pull_request", "push", "release"]

        webhook_config = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0",
            },
        }

        try:
            logger.info(f"Creating webhook for {owner}/{repo}")
            return await self._request(
                "POST", f"/repos/{owner}/{repo}/hooks", json=webhook_config
            )
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise

    async def list_webhooks(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List repository webhooks."""
        if not self.token:
            raise ValueError("GitHub token required for webhook listing")

        try:
            return await self._request("GET", f"/repos/{owner}/{repo}/hooks")
        except Exception as e:
            logger.error(f"Error listing webhooks: {e}")
            return []

    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> bool:
        """Delete a repository webhook."""
        if not self.token:
            raise ValueError("GitHub token required for webhook deletion")

        try:
            await self._request("DELETE", f"/repos/{owner}/{repo}/hooks/{hook_id}")
            logger.info(f"Deleted webhook {hook_id} for {owner}/{repo}")
            return True
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    async def test_webhook(self, owner: str, repo: str, hook_id: int) -> bool:
        """Test a repository webhook."""
        if not self.token:
            raise ValueError("GitHub token required for webhook testing")

        try:
            await self._request("POST", f"/repos/{owner}/{repo}/hooks/{hook_id}/tests")
            logger.info(f"Webhook test triggered for {owner}/{repo}")
            return True
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return False

    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        if not self.token:
            raise ValueError("GitHub token required for user info")

        return await self._request("GET", "/user")

    async def check_token_permissions(self) -> Dict[str, Any]:
        """Check GitHub token permissions."""
        if not self.token:
            return {"valid": False, "error": "No token provided"}

        try:
            user_info = await self.get_user_info()

            # Try to access a repository to check repo permissions
            # This is a simplified check - in practice you'd want more specific validation

            return {
                "valid": True,
                "user": user_info.get("login", "unknown"),
                "scopes": user_info.get("scopes", []),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def parse_repository_url(self, repo_url: str) -> tuple[str, str]:
        """Parse repository URL to extract owner and repo name."""
        # Handle various GitHub URL formats
        import re

        patterns = [
            r"github\.com[:/]([^/]+)/([^/.]+)",  # git@github.com:owner/repo or https://github.com/owner/repo
            r"^([^/]+)/([^/]+)$",  # owner/repo
        ]

        for pattern in patterns:
            match = re.search(pattern, repo_url)
            if match:
                return match.group(1), match.group(2)

        raise ValueError(f"Could not parse repository URL: {repo_url}")

    async def auto_detect_repository(self) -> Optional[tuple[str, str]]:
        """Auto-detect current repository from git remote."""
        try:

            import asyncio

            process = await asyncio.create_subprocess_exec(
                "git",
                "remote",
                "get-url",
                "origin",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                remote_url = stdout.decode().strip()
                return await self.parse_repository_url(remote_url)
            return None

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                return await self.parse_repository_url(remote_url)
        except Exception as e:
            logger.debug(f"Could not auto-detect repository: {e}")

        return None
