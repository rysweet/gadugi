"""
Example Usage of Code Reviewer V0.3 Agent
========================================

This example demonstrates how to use the Code Reviewer V0.3 agent
for various code review tasks with learning capabilities.
"""

import asyncio
import json
import tempfile
from pathlib import Path

# Import the agent
from code_reviewer_v03 import CodeReviewerV03


async def example_basic_review():
    """Example: Basic file review with learning."""
    print("\n" + "="*60)
    print("Example 1: Basic Code Review")
    print("="*60)

    # Create reviewer agent
    reviewer = CodeReviewerV03()
    test_files = []  # Initialize before try block

    try:
        # Initialize with memory system (would connect to actual MCP in production)
        await reviewer.initialize()

        # Start a review task
        task_id = await reviewer.start_task("Review Python files for PR #123")
        print(f"🚀 Started review task: {task_id}")

        # Create sample files to review
        test_files = await create_sample_files()

        # Execute review
        review_task = {
            "type": "review_files",
            "files": test_files,
            "author": "alice_developer",
            "description": "Added new feature with validation"
        }

        outcome = await reviewer.execute_task(review_task)

        if outcome.success:
            print("✅ Review completed successfully!")
            print(f"⏱️  Duration: {outcome.duration_seconds:.2f} seconds")
            print(f"📝 Steps taken: {len(outcome.steps_taken)}")
            for step in outcome.steps_taken:
                print(f"   - {step}")
        else:
            print(f"❌ Review failed: {outcome.error}")

        # Learn from the outcome
        await reviewer.learn_from_outcome(outcome)

    finally:
        await reviewer.shutdown()
        # Clean up test files
        for file_path in test_files:
            try:
                Path(file_path).unlink()
            except:
                pass


async def example_learning_from_feedback():
    """Example: Learning from human feedback on reviews."""
    print("\n" + "="*60)
    print("Example 2: Learning from Feedback")
    print("="*60)

    reviewer = CodeReviewerV03()

    try:
        await reviewer.initialize()
        task_id = await reviewer.start_task("Learn from previous review feedback")

        # Simulate feedback from developers about previous reviews
        feedback_data = [
            {
                "issue_id": "review_123_issue_1",
                "rule_id": "E501",  # Line too long
                "issue_type": "warning",
                "category": "style",
                "developer": "alice_developer",
                "file_path": "src/validation.py",
                "accepted": False,
                "reason": "Our team prefers longer lines for readability in this module"
            },
            {
                "issue_id": "review_123_issue_2",
                "rule_id": "F401",  # Unused import
                "issue_type": "error",
                "category": "quality",
                "developer": "alice_developer",
                "file_path": "src/validation.py",
                "accepted": True,
                "reason": "Good catch! Removed the unused import."
            },
            {
                "issue_id": "review_124_issue_1",
                "rule_id": "S101",  # Use of assert
                "issue_type": "warning",
                "category": "security",
                "developer": "bob_developer",
                "file_path": "src/auth.py",
                "accepted": True,
                "reason": "You're right, replaced with proper exception"
            },
            {
                "issue_id": "review_124_issue_2",
                "rule_id": "E501",  # Line too long (again)
                "issue_type": "warning",
                "category": "style",
                "developer": "bob_developer",
                "file_path": "src/auth.py",
                "accepted": False,
                "reason": "This is a complex SQL query that's more readable on one line"
            }
        ]

        # Learn from feedback
        learning_task = {
            "type": "learn_from_feedback",
            "feedback": feedback_data
        }

        outcome = await reviewer.execute_task(learning_task)

        if outcome.success:
            print("✅ Learning completed!")
            print(f"📊 Learned from {len(feedback_data)} feedback items")

            # Show what the agent learned about each developer
            print("\n📚 Developer Insights:")

            for developer in ["alice_developer", "bob_developer"]:
                insights = await reviewer.get_developer_insights(developer)
                if "message" not in insights:  # Has pattern data
                    print(f"\n👤 {developer}:")
                    print(f"   Common issues: {insights['common_issues']}")
                    print(f"   Ignored rules: {insights['ignored_rules']}")
                    print(f"   Total reviews: {insights['total_reviews']}")

        await reviewer.learn_from_outcome(outcome)

    finally:
        await reviewer.shutdown()


async def example_adaptive_scoring():
    """Example: Demonstrating adaptive scoring based on learned patterns."""
    print("\n" + "="*60)
    print("Example 3: Adaptive Scoring with Patterns")
    print("="*60)

    reviewer = CodeReviewerV03()

    try:
        await reviewer.initialize()

        # First, establish some patterns by learning from feedback
        print("🧠 Establishing developer patterns...")

        # Alice ignores line length but cares about security
        alice_feedback = [
            {"issue_id": "1", "rule_id": "E501", "developer": "alice", "file_path": "test.py", "accepted": False},
            {"issue_id": "2", "rule_id": "E501", "developer": "alice", "file_path": "test.py", "accepted": False},
            {"issue_id": "3", "rule_id": "S102", "developer": "alice", "file_path": "test.py", "accepted": True},
            {"issue_id": "4", "rule_id": "F401", "developer": "alice", "file_path": "test.py", "accepted": True},
        ]

        # Bob is the opposite - cares about style but sometimes ignores minor security
        bob_feedback = [
            {"issue_id": "5", "rule_id": "E501", "developer": "bob", "file_path": "test.py", "accepted": True},
            {"issue_id": "6", "rule_id": "E501", "developer": "bob", "file_path": "test.py", "accepted": True},
            {"issue_id": "7", "rule_id": "S101", "developer": "bob", "file_path": "test.py", "accepted": False},
            {"issue_id": "8", "rule_id": "W292", "developer": "bob", "file_path": "test.py", "accepted": True},
        ]

        # Learn from both developers
        for feedback_set in [alice_feedback, bob_feedback]:
            learning_task = {"type": "learn_from_feedback", "feedback": feedback_set}
            await reviewer.execute_task(learning_task)

        # Now review the same files for each developer - adaptive scoring should differ
        test_files = await create_sample_files()

        print("\n📊 Reviewing same code for different developers:")

        for developer in ["alice", "bob"]:
            print(f"\n👤 Review for {developer}:")

            task_id = await reviewer.start_task(f"Adaptive review for {developer}")

            review_task = {
                "type": "review_files",
                "files": test_files,
                "author": developer
            }

            outcome = await reviewer.execute_task(review_task)

            if outcome.success:
                # In a real implementation, the adaptive scoring would be visible
                # in the review results and recommendations
                print(f"   ✅ Review completed with adaptive scoring")
                print(f"   📝 Custom recommendations generated based on {developer}'s patterns")

                # Show developer-specific insights
                insights = await reviewer.get_developer_insights(developer)
                if "message" not in insights:
                    print(f"   🎯 Ignored rules: {list(insights['ignored_rules'])}")
                    print(f"   ⚠️  Common issues: {list(insights['common_issues'].keys())}")

        # Clean up
        for file_path in test_files:
            try:
                Path(file_path).unlink()
            except:
                pass

    finally:
        await reviewer.shutdown()


async def example_pattern_analysis():
    """Example: Analyzing patterns across the team."""
    print("\n" + "="*60)
    print("Example 4: Team Pattern Analysis")
    print("="*60)

    reviewer = CodeReviewerV03()

    try:
        await reviewer.initialize()

        # Simulate historical review data for pattern analysis
        print("📊 Simulating historical review data...")

        # Create diverse feedback patterns for analysis
        historical_feedback = [
            # Team tends to ignore certain style rules
            {"issue_id": "h1", "rule_id": "E501", "developer": "alice", "file_path": "ui/forms.py", "accepted": False},
            {"issue_id": "h2", "rule_id": "E501", "developer": "bob", "file_path": "ui/views.py", "accepted": False},
            {"issue_id": "h3", "rule_id": "E501", "developer": "carol", "file_path": "ui/models.py", "accepted": False},

            # But security issues are always accepted
            {"issue_id": "h4", "rule_id": "S102", "developer": "alice", "file_path": "auth/views.py", "accepted": True},
            {"issue_id": "h5", "rule_id": "S108", "developer": "bob", "file_path": "auth/models.py", "accepted": True},
            {"issue_id": "h6", "rule_id": "S601", "developer": "carol", "file_path": "auth/utils.py", "accepted": True},

            # Certain modules have recurring issues
            {"issue_id": "h7", "rule_id": "C901", "developer": "alice", "file_path": "legacy/processor.py", "accepted": True},
            {"issue_id": "h8", "rule_id": "C901", "developer": "bob", "file_path": "legacy/processor.py", "accepted": True},
            {"issue_id": "h9", "rule_id": "F401", "developer": "carol", "file_path": "legacy/utils.py", "accepted": True},

            # Performance issues in data processing modules
            {"issue_id": "h10", "rule_id": "PERF101", "developer": "alice", "file_path": "data/pipeline.py", "accepted": True},
            {"issue_id": "h11", "rule_id": "PERF102", "developer": "bob", "file_path": "data/transform.py", "accepted": True},
        ]

        # Learn from historical data
        learning_task = {"type": "learn_from_feedback", "feedback": historical_feedback}
        outcome = await reviewer.execute_task(learning_task)

        print(f"✅ Learned from {len(historical_feedback)} historical reviews")

        # Analyze patterns
        print("\n🔍 Analyzing team patterns...")

        analysis_task = {"type": "analyze_patterns"}
        outcome = await reviewer.execute_task(analysis_task)

        if outcome.success:
            print("✅ Pattern analysis completed!")

            # Show insights for each developer
            print("\n👥 Developer Patterns:")
            for developer in ["alice", "bob", "carol"]:
                insights = await reviewer.get_developer_insights(developer)
                if "message" not in insights:
                    print(f"\n👤 {developer}:")
                    print(f"   📈 Total reviews: {insights['total_reviews']}")
                    print(f"   ⚠️  Common issues: {dict(list(insights['common_issues'].items())[:3])}")
                    print(f"   🙈 Ignored rules: {list(insights['ignored_rules'])[:3]}")

            # Show module patterns
            print("\n📁 Module Patterns:")
            interesting_modules = ["legacy/processor.py", "auth/views.py", "data/pipeline.py"]
            for module in interesting_modules:
                insights = await reviewer.get_module_insights(module)
                if "message" not in insights:
                    print(f"\n📄 {module}:")
                    print(f"   🐛 Total issues: {insights['total_issues']}")
                    print(f"   🔥 Frequent issues: {dict(list(insights['frequent_issues'].items())[:3])}")
                    print(f"   🔒 Security hotspot: {insights['is_security_hotspot']}")

    finally:
        await reviewer.shutdown()


async def example_production_workflow():
    """Example: Production-like workflow with comprehensive review."""
    print("\n" + "="*60)
    print("Example 5: Production Workflow")
    print("="*60)

    reviewer = CodeReviewerV03()

    try:
        await reviewer.initialize()

        print("🚀 Starting production-like code review workflow...")

        # Step 1: Create realistic test files
        test_files = await create_production_like_files()

        # Step 2: Comprehensive review
        task_id = await reviewer.start_task("Production code review for feature/user-auth")

        review_task = {
            "type": "review_files",
            "files": test_files,
            "author": "senior_dev",
            "description": "Implementing OAuth2 authentication with rate limiting"
        }

        print("🔍 Executing comprehensive review...")
        outcome = await reviewer.execute_task(review_task)

        if outcome.success:
            print("✅ Review completed!")
            print(f"⏱️  Duration: {outcome.duration_seconds:.2f} seconds")

            # In production, this would generate a detailed report
            print("\n📊 Review Summary (simulated):")
            print("   - Security analysis: ✅ Passed")
            print("   - Performance check: ✅ Passed")
            print("   - Code quality: ⚠️  Minor issues found")
            print("   - Test coverage: ✅ Adequate")

            # Step 3: Collaborative decision making
            print("\n🤝 Recording review decision...")
            await reviewer.collaborate(
                "Code review completed for OAuth2 implementation. "
                "Minor style issues identified but security and performance look good.",
                decision="APPROVE_WITH_SUGGESTIONS"
            )

        # Step 4: Learn from the review
        await reviewer.learn_from_outcome(outcome)

        # Step 5: Generate team insights
        insights = await reviewer.get_developer_insights("senior_dev")
        if "message" not in insights:
            print(f"\n👤 Developer Pattern for senior_dev:")
            print(f"   📊 Reviews participated: {insights['total_reviews']}")
            print(f"   🎯 Focus areas: {list(insights['common_issues'].keys())[:3]}")

        # Clean up
        for file_path in test_files:
            try:
                Path(file_path).unlink()
            except:
                pass

    finally:
        await reviewer.shutdown()


async def create_sample_files():
    """Create sample Python files for testing."""
    files = []

    # File 1: Basic validation module
    validation_content = '''
"""User input validation module."""

def validate_email(email):
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit

def process_user_data(data):
    """Process user registration data."""
    if not data:
        return None

    email = data.get('email')
    password = data.get('password')

    if not validate_email(email):
        raise ValueError("Invalid email")
    if not validate_password(password):
        raise ValueError("Weak password")

    return {
        'email': email.lower(),
        'password_hash': hash_password(password)
    }

def hash_password(password):
    """Hash password for storage."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='_validation.py', delete=False) as f:
        f.write(validation_content)
        files.append(f.name)

    # File 2: API utilities with some issues
    api_content = '''
"""API utility functions."""

import requests
import json

def fetch_user_data(user_id):
    """Fetch user data from external API."""
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def batch_fetch_users(user_ids):
    """Fetch multiple users - potential N+1 problem."""
    users = []
    for user_id in user_ids:  # This creates N requests
        user_data = fetch_user_data(user_id)
        if user_data:
            users.append(user_data)
    return users

class APIClient:
    """API client with some issues."""

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def make_request(self, endpoint, method="GET", data=None):
        """Make API request - needs error handling."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)

        return response.json()  # May fail if not JSON
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='_api.py', delete=False) as f:
        f.write(api_content)
        files.append(f.name)

    return files


async def create_production_like_files():
    """Create more realistic production-like files for comprehensive testing."""
    files = []

    # Authentication module
    auth_content = '''
"""OAuth2 authentication implementation."""

import secrets
import hashlib
import time
from typing import Optional, Dict, Any

class OAuth2Handler:
    """OAuth2 authentication handler."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_store = {}  # In production, use proper storage

    def generate_auth_code(self, user_id: str) -> str:
        """Generate authorization code."""
        auth_code = secrets.token_urlsafe(32)
        self.token_store[auth_code] = {
            'user_id': user_id,
            'expires': time.time() + 600,  # 10 minutes
            'type': 'auth_code'
        }
        return auth_code

    def exchange_code_for_token(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        if auth_code not in self.token_store:
            return None

        code_data = self.token_store[auth_code]

        if time.time() > code_data['expires']:
            del self.token_store[auth_code]
            return None

        # Generate access token
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        self.token_store[access_token] = {
            'user_id': code_data['user_id'],
            'expires': time.time() + 3600,  # 1 hour
            'type': 'access_token'
        }

        self.token_store[refresh_token] = {
            'user_id': code_data['user_id'],
            'expires': time.time() + 86400,  # 24 hours
            'type': 'refresh_token'
        }

        # Clean up auth code
        del self.token_store[auth_code]

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }

    def validate_token(self, token: str) -> Optional[str]:
        """Validate access token and return user_id."""
        if token not in self.token_store:
            return None

        token_data = self.token_store[token]

        if time.time() > token_data['expires']:
            del self.token_store[token]
            return None

        return token_data['user_id']

def hash_client_secret(secret: str) -> str:
    """Hash client secret for secure storage."""
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, 100000)
    return salt + key
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='_oauth.py', delete=False) as f:
        f.write(auth_content)
        files.append(f.name)

    # Rate limiting module
    rate_limit_content = '''
"""Rate limiting implementation."""

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.buckets: Dict[str, Tuple[float, int]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()

        with self.lock:
            if identifier not in self.buckets:
                self.buckets[identifier] = (now, self.max_requests - 1)
                return True

            last_refill, tokens = self.buckets[identifier]

            # Calculate tokens to add based on time elapsed
            elapsed = now - last_refill
            tokens_to_add = int(elapsed / self.window_seconds * self.max_requests)

            if tokens_to_add > 0:
                tokens = min(self.max_requests, tokens + tokens_to_add)
                last_refill = now

            if tokens > 0:
                self.buckets[identifier] = (last_refill, tokens - 1)
                return True
            else:
                self.buckets[identifier] = (last_refill, tokens)
                return False

    def cleanup_old_buckets(self):
        """Clean up old bucket entries."""
        now = time.time()
        cutoff = now - self.window_seconds * 2

        with self.lock:
            expired_keys = [
                key for key, (last_refill, _) in self.buckets.items()
                if last_refill < cutoff
            ]

            for key in expired_keys:
                del self.buckets[key]

class IPRateLimiter(RateLimiter):
    """IP-based rate limiter."""

    def __init__(self):
        super().__init__(max_requests=60, window_seconds=60)  # 60 requests per minute

    def check_ip_limit(self, ip_address: str) -> bool:
        """Check rate limit for IP address."""
        return self.is_allowed(ip_address)

class UserRateLimiter(RateLimiter):
    """User-based rate limiter."""

    def __init__(self):
        super().__init__(max_requests=1000, window_seconds=3600)  # 1000 requests per hour

    def check_user_limit(self, user_id: str) -> bool:
        """Check rate limit for user."""
        return self.is_allowed(user_id)
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='_rate_limit.py', delete=False) as f:
        f.write(rate_limit_content)
        files.append(f.name)

    return files


async def main():
    """Run all examples."""
    print("🎯 Code Reviewer V0.3 Agent Examples")
    print("=" * 60)

    examples = [
        ("Basic Review", example_basic_review),
        ("Learning from Feedback", example_learning_from_feedback),
        ("Adaptive Scoring", example_adaptive_scoring),
        ("Pattern Analysis", example_pattern_analysis),
        ("Production Workflow", example_production_workflow),
    ]

    for name, example_func in examples:
        try:
            print(f"\n🚀 Running: {name}")
            await example_func()
            print(f"✅ {name} completed successfully!")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n🏁 All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
