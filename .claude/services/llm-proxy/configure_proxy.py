#!/usr/bin/env python3
"""
Interactive configuration wizard for LLM Proxy Service.
Helps users set up providers and start the service with proper logging.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import getpass

class LLMProxyConfigurator:
    """Interactive configuration wizard for LLM Proxy Service."""
    
    PROVIDERS = {
        "azure_openai": {
            "name": "Azure OpenAI",
            "env_prefix": "AZURE_OPENAI",
            "required_fields": [
                ("api_key", "Azure OpenAI API Key", True, None),
                ("endpoint", "Azure Endpoint (e.g., https://YOUR-RESOURCE.openai.azure.com/)", False, None),
                ("api_version", "API Version", False, "2024-02-15-preview"),
                ("deployment_name", "Deployment Name", False, None)
            ],
            "models": ["gpt-4", "gpt-3.5-turbo"]
        },
        "openai": {
            "name": "OpenAI",
            "env_prefix": "OPENAI",
            "required_fields": [
                ("api_key", "OpenAI API Key", True, None),
                ("org_id", "Organization ID (optional)", False, "")
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "env_prefix": "ANTHROPIC",
            "required_fields": [
                ("api_key", "Anthropic API Key", True, None)
            ],
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        },
        "google": {
            "name": "Google Gemini",
            "env_prefix": "GOOGLE",
            "required_fields": [
                ("api_key", "Google AI API Key", True, None)
            ],
            "models": ["gemini-pro", "gemini-pro-vision"]
        },
        "ollama": {
            "name": "Ollama (Local)",
            "env_prefix": "OLLAMA",
            "required_fields": [
                ("host", "Ollama Host URL", False, "http://localhost:11434")
            ],
            "models": ["llama2", "mistral", "codellama"]
        }
    }
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.env_file = self.base_dir / ".env"
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self):
        """Run the configuration wizard."""
        self.print_header()
        
        # Select provider
        provider = self.select_provider()
        if not provider:
            print("\n👋 Configuration cancelled.")
            return
        
        # Collect configuration
        config = self.collect_configuration(provider)
        if not config:
            print("\n❌ Configuration incomplete.")
            return
        
        # Save configuration
        self.save_configuration(provider, config)
        
        # Test configuration (optional)
        if self.ask_yes_no("\nWould you like to test the configuration?"):
            if not self.test_configuration(provider, config):
                if not self.ask_yes_no("Test failed. Continue anyway?", default=False):
                    return
        
        # Offer to start service
        if self.ask_yes_no("\nWould you like to start the LLM Proxy service now?"):
            self.start_service()
        else:
            self.show_manual_start_instructions()
    
    def print_header(self):
        """Print wizard header."""
        print("\n" + "="*60)
        print("🤖 LLM Proxy Configuration Wizard")
        print("="*60)
        print("\nThis wizard will help you configure LLM providers for the")
        print("proxy service and set up background logging.\n")
    
    def select_provider(self) -> Optional[str]:
        """Let user select a provider."""
        print("📋 Available providers:")
        print("-" * 40)
        providers = list(self.PROVIDERS.keys())
        for i, key in enumerate(providers, 1):
            provider_info = self.PROVIDERS[key]
            print(f"  {i}. {provider_info['name']}")
            print(f"     Models: {', '.join(provider_info['models'][:3])}")
        
        print("\n  0. Configure multiple providers")
        print("  q. Quit")
        
        while True:
            try:
                choice = input("\n➤ Select provider (number): ").strip().lower()
                if choice == 'q':
                    return None
                if choice == '0':
                    return self.configure_multiple_providers()
                    
                idx = int(choice) - 1
                if 0 <= idx < len(providers):
                    return providers[idx]
            except (ValueError, IndexError):
                pass
            print("❌ Invalid choice. Please try again.")
    
    def configure_multiple_providers(self) -> Optional[str]:
        """Configure multiple providers."""
        print("\n🔄 Multiple Provider Configuration")
        print("Configure providers one by one. The service will load balance between them.")
        
        configured = []
        while True:
            provider = self.select_provider()
            if not provider:
                break
                
            config = self.collect_configuration(provider)
            if config:
                self.save_configuration(provider, config)
                configured.append(provider)
                
            if not self.ask_yes_no("\nAdd another provider?", default=False):
                break
        
        if configured:
            print(f"\n✅ Configured {len(configured)} providers: {', '.join(configured)}")
            return "multiple"
        return None
    
    def collect_configuration(self, provider: str) -> Optional[Dict[str, Any]]:
        """Collect configuration for the selected provider."""
        provider_info = self.PROVIDERS[provider]
        
        print(f"\n⚙️  Configuring {provider_info['name']}")
        print("-" * 50)
        
        config = {
            "provider": provider,
            "name": provider_info['name'],
            "timestamp": datetime.now().isoformat()
        }
        env_vars = {}
        
        # Collect required fields
        for field_info in provider_info["required_fields"]:
            field, prompt, is_secret, default = field_info
            
            # Build environment variable name
            env_var_name = f"{provider_info['env_prefix']}_{field.upper()}"
            
            # Check if already in environment
            existing_value = os.getenv(env_var_name)
            if existing_value:
                if is_secret:
                    print(f"✓ {prompt}: [Using existing environment variable]")
                    value = existing_value
                else:
                    use_existing = self.ask_yes_no(
                        f"{prompt}\n  Current value: {existing_value}\n  Use this value?",
                        default=True
                    )
                    if use_existing:
                        value = existing_value
                    else:
                        value = self.get_input(prompt, is_secret, default)
            else:
                value = self.get_input(prompt, is_secret, default)
            
            if not value and not default:
                if field != "org_id":  # Optional field
                    print(f"❌ {prompt} is required.")
                    return None
            
            if value:
                config[field] = value
                env_vars[env_var_name] = value
        
        # Additional settings
        print("\n📊 Additional Settings (press Enter for defaults):")
        config["cache_enabled"] = self.ask_yes_no("  Enable response caching?", True)
        config["rate_limit"] = self.get_number("  Rate limit (requests/minute)", 60)
        config["max_retries"] = self.get_number("  Max retries on failure", 3)
        config["timeout"] = self.get_number("  Request timeout (seconds)", 30)
        
        # Model selection
        if provider_info.get("models"):
            print(f"\n🎯 Available models: {', '.join(provider_info['models'])}")
            selected_model = input(f"  Primary model [{provider_info['models'][0]}]: ").strip()
            config["primary_model"] = selected_model or provider_info['models'][0]
        
        config["env_vars"] = env_vars
        return config
    
    def get_input(self, prompt: str, is_secret: bool, default: Optional[str]) -> str:
        """Get input from user."""
        if is_secret:
            return getpass.getpass(f"  🔐 {prompt}: ").strip()
        else:
            prompt_text = f"  ➤ {prompt}"
            if default:
                prompt_text += f" [{default}]"
            prompt_text += ": "
            value = input(prompt_text).strip()
            return value if value else default
    
    def get_number(self, prompt: str, default: int) -> int:
        """Get numeric input from user."""
        while True:
            try:
                value = input(f"{prompt} [{default}]: ").strip()
                return int(value) if value else default
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def save_configuration(self, provider: str, config: Dict[str, Any]):
        """Save configuration to files."""
        # Save JSON config
        config_file = self.config_dir / f"{provider}.json"
        env_vars = config.pop("env_vars", {})
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Configuration saved to: {config_file.relative_to(Path.cwd())}")
        
        # Update .env file
        self.update_env_file(env_vars)
    
    def update_env_file(self, env_vars: Dict[str, str]):
        """Update .env file with new variables."""
        existing = {}
        
        # Read existing values
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing[key] = value
        
        # Update with new values
        existing.update(env_vars)
        
        # Add service defaults if not present
        defaults = {
            "LLM_PROXY_PORT": "8080",
            "LLM_PROXY_LOG_LEVEL": "INFO",
            "LLM_PROXY_CACHE_SIZE": "1000",
            "LLM_PROXY_CACHE_TTL": "3600",
            "LLM_PROXY_MAX_WORKERS": "10"
        }
        
        for key, value in defaults.items():
            if key not in existing:
                existing[key] = value
        
        # Set log file path
        log_file = self.log_dir / f"llm_proxy_{datetime.now().strftime('%Y%m%d')}.log"
        existing["LLM_PROXY_LOG_FILE"] = str(log_file)
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.write("# LLM Proxy Service Configuration\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            # Provider settings
            f.write("# Provider API Keys and Settings\n")
            for key in sorted(existing.keys()):
                if any(prefix in key for prefix in ["AZURE", "OPENAI", "ANTHROPIC", "GOOGLE", "OLLAMA"]):
                    # Mask API keys in comments
                    if "API_KEY" in key:
                        f.write(f"# {key}=<configured>\n")
                        f.write(f"{key}={existing[key]}\n")
                    else:
                        f.write(f"{key}={existing[key]}\n")
            
            f.write("\n# Service Configuration\n")
            for key in sorted(existing.keys()):
                if "LLM_PROXY" in key:
                    f.write(f"{key}={existing[key]}\n")
        
        print(f"✅ Environment saved to: {self.env_file.relative_to(Path.cwd())}")
    
    def test_configuration(self, provider: str, config: Dict[str, Any]) -> bool:
        """Test the configuration by making a simple request."""
        print("\n🧪 Testing configuration...")
        
        # Create a simple test script
        test_script = self.base_dir / "test_config.py"
        test_code = f"""
import os
import sys
import asyncio
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv('{self.env_file}')

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

async def test():
    try:
        from llm_proxy_service import LLMProxyService, create_completion_request
        
        service = LLMProxyService()
        await service.start()
        
        request = create_completion_request(
            prompt="Say 'Configuration test successful!'",
            model="{config.get('primary_model', 'gpt-3.5-turbo')}",
            max_tokens=10
        )
        
        response = await service.generate_completion(request)
        print("✅ Test successful! Response:", response.content[:50])
        await service.stop()
        return True
    except Exception as e:
        print(f"❌ Test failed: {{e}}")
        return False

asyncio.run(test())
"""
        
        with open(test_script, 'w') as f:
            f.write(test_code)
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                print("✅ Configuration test passed!")
            else:
                print(f"❌ Test failed: {result.stderr}")
            return success
        except subprocess.TimeoutExpired:
            print("❌ Test timed out.")
            return False
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
        finally:
            test_script.unlink(missing_ok=True)
    
    def start_service(self):
        """Start the LLM Proxy service in the background."""
        print("\n🚀 Starting LLM Proxy Service...")
        
        # Create launch script if it doesn't exist
        launch_script = self.base_dir / "launch_proxy.py"
        if not launch_script.exists():
            self.create_launch_script(launch_script)
        
        # Create unique log file for this session
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f"llm_proxy_{timestamp}.log"
        
        # Start service in background
        try:
            process = subprocess.Popen(
                [sys.executable, str(launch_script)],
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={**os.environ, "LLM_PROXY_LOG_FILE": str(log_file)}
            )
            
            # Save PID
            pid_file = self.base_dir / "llm_proxy.pid"
            pid_file.write_text(str(process.pid))
            
            # Wait a moment to check if it started successfully
            import time
            time.sleep(2)
            
            if process.poll() is None:
                self.print_success_message(process.pid, log_file)
            else:
                print(f"\n❌ Service failed to start. Check logs: {log_file}")
                with open(log_file) as f:
                    print(f.read()[-500:])  # Show last 500 chars of error
                    
        except Exception as e:
            print(f"\n❌ Failed to start service: {e}")
    
    def create_launch_script(self, launch_script: Path):
        """Create the launch script for the service."""
        script_content = '''#!/usr/bin/env python3
"""Launch script for LLM Proxy Service."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment
from dotenv import load_dotenv
env_file = Path(__file__).parent / ".env"
load_dotenv(env_file)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from llm_proxy_service import (
    LLMProxyService, LoadBalanceStrategy,
    ModelConfig, LLMProvider
)

# Setup logging
log_file = os.getenv("LLM_PROXY_LOG_FILE", 
                     f"logs/llm_proxy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
log_dir = Path(log_file).parent
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LLM_PROXY_LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Launch the LLM Proxy Service."""
    
    logger.info("="*60)
    logger.info("Starting LLM Proxy Service")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Configuration: {env_file}")
    logger.info("="*60)
    
    # Create service
    service = LLMProxyService(
        cache_size=int(os.getenv("LLM_PROXY_CACHE_SIZE", "1000")),
        cache_ttl=int(os.getenv("LLM_PROXY_CACHE_TTL", "3600")),
        load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
        enable_failover=True,
        max_retries=int(os.getenv("LLM_PROXY_MAX_RETRIES", "3"))
    )
    
    # Auto-detect and configure providers from environment
    providers_configured = []
    
    # Check for Azure OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        logger.info("Configuring Azure OpenAI provider...")
        # Add Azure configuration
        providers_configured.append("Azure OpenAI")
    
    # Check for OpenAI
    if os.getenv("OPENAI_API_KEY"):
        logger.info("Configuring OpenAI provider...")
        # Add OpenAI configuration
        providers_configured.append("OpenAI")
    
    # Check for Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("Configuring Anthropic provider...")
        # Add Anthropic configuration
        providers_configured.append("Anthropic")
    
    logger.info(f"Configured providers: {', '.join(providers_configured)}")
    
    try:
        # Start service
        await service.start()
        logger.info("LLM Proxy Service started successfully")
        logger.info(f"Port: {os.getenv('LLM_PROXY_PORT', '8080')}")
        
        # Keep running and log statistics
        while True:
            await asyncio.sleep(60)
            stats = service.get_service_stats()
            logger.info(f"Stats - Requests: {stats.get('total_requests', 0)}, "
                       f"Cache hits: {stats.get('cache_hits', 0)}, "
                       f"Errors: {stats.get('total_errors', 0)}")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
    finally:
        await service.stop()
        logger.info("LLM Proxy Service stopped")
        logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(launch_script, 'w') as f:
            f.write(script_content)
        launch_script.chmod(0o755)
    
    def print_success_message(self, pid: int, log_file: Path):
        """Print success message with monitoring instructions."""
        print("\n" + "="*60)
        print("✅ LLM Proxy Service Started Successfully!")
        print("="*60)
        
        print(f"\n📌 Service Information:")
        print(f"   PID: {pid}")
        print(f"   Status: Running")
        print(f"   Port: {os.getenv('LLM_PROXY_PORT', '8080')}")
        
        print(f"\n📁 Log File Location:")
        print(f"   {log_file}")
        
        print(f"\n📊 To monitor logs in real-time, copy and run this command:")
        print(f"   tail -f {log_file}")
        
        print(f"\n🔍 Service Management Commands:")
        print(f"   Check status:  ps -p {pid}")
        print(f"   View logs:     tail -n 50 {log_file}")
        print(f"   Stop service:  kill {pid}")
        print(f"   Restart:       python3 {self.base_dir}/launch_proxy.py")
        
        print("\n💡 The service is now running in the background and will")
        print("   continue even after you close this terminal.")
        print("="*60)
    
    def show_manual_start_instructions(self):
        """Show instructions for manually starting the service."""
        print("\n📝 To start the service manually later, run:")
        print(f"   python3 {self.base_dir}/launch_proxy.py &")
        print("\nOr use the configuration wizard again:")
        print(f"   python3 {self.base_dir}/configure_proxy.py")
    
    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Ask a yes/no question."""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print("Please answer 'y' or 'n'")


def main():
    """Main entry point."""
    try:
        # Check for required dependencies
        try:
            import dotenv
        except ImportError:
            print("Installing required dependency: python-dotenv")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
            import dotenv
        
        configurator = LLMProxyConfigurator()
        configurator.run()
    except KeyboardInterrupt:
        print("\n\n👋 Configuration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()