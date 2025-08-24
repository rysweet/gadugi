# LLM Proxy Service Configuration & Management

The LLM Proxy Service provides a unified interface to multiple LLM providers with automatic failover, caching, and load balancing. This directory contains both the service implementation and interactive configuration tools.

## Quick Start

### Using the LLM Proxy Agent

The easiest way to configure the LLM Proxy is through the dedicated agent:

```
/agent:llm-proxy-agent

Help me set up Azure OpenAI with the LLM Proxy
```

The agent will:
1. Walk you through configuration step-by-step
2. Securely collect your API credentials
3. Save configuration to `.env` and JSON files
4. Start the service in the background
5. Provide you with log monitoring commands

### Manual Configuration

You can also run the configuration wizard directly:

```bash
python3 .claude/services/llm-proxy/configure_proxy.py
```

## Supported Providers

| Provider | Environment Variables | Models |
|----------|----------------------|--------|
| **Azure OpenAI** | `AZURE_OPENAI_API_KEY`<br>`AZURE_OPENAI_ENDPOINT`<br>`AZURE_OPENAI_API_VERSION`<br>`AZURE_OPENAI_DEPLOYMENT_NAME` | gpt-4, gpt-3.5-turbo |
| **OpenAI** | `OPENAI_API_KEY`<br>`OPENAI_ORG_ID` (optional) | gpt-4, gpt-3.5-turbo, gpt-4-turbo |
| **Anthropic** | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| **Google Gemini** | `GOOGLE_API_KEY` | gemini-pro, gemini-pro-vision |
| **Ollama** | `OLLAMA_HOST` | llama2, mistral, codellama |

## Configuration Wizard Features

### Interactive Setup
- Step-by-step provider configuration
- Secure password input for API keys
- Default values for common settings
- Multiple provider support

### Automatic Service Management
- Starts service in background
- Creates timestamped log files
- Provides monitoring commands
- Saves PID for service control

### Time-Based Scheduling (NEW!)
- Run until specific time (e.g., "until 7:00 PM")
- Run for duration (e.g., "for 2 hours")
- Run until tomorrow at specific time
- Automatic shutdown at scheduled time
- Cancel or modify schedule anytime

### Configuration Testing
- Validates API keys before starting
- Tests provider connectivity
- Provides clear error messages

## File Structure

```
.claude/services/llm-proxy/
├── llm_proxy_service.py    # Main service implementation
├── configure_proxy.py      # Interactive configuration wizard
├── launch_proxy.py         # Service launcher (auto-generated)
├── config/                 # Provider configurations (JSON)
│   ├── azure_openai.json
│   ├── openai.json
│   └── anthropic.json
├── logs/                   # Service logs
│   └── llm_proxy_*.log
├── .env                    # Environment variables
└── llm_proxy.pid          # Process ID when running
```

## Usage Examples

### Example 1: Configure Azure OpenAI

```bash
$ python3 configure_proxy.py

🤖 LLM Proxy Configuration Wizard
============================================

📋 Available providers:
  1. Azure OpenAI
  2. OpenAI
  3. Anthropic Claude
  ...

➤ Select provider: 1

⚙️ Configuring Azure OpenAI
🔐 API Key: ****
➤ Endpoint: https://my-resource.openai.azure.com/
➤ API Version [2024-02-15-preview]: 
➤ Deployment Name: gpt-4-deployment

✅ Configuration saved!
🚀 Starting LLM Proxy Service...

✅ Service Started Successfully!
📁 Log file: logs/llm_proxy_20240124_143022.log
📊 To monitor: tail -f logs/llm_proxy_20240124_143022.log
```

### Example 2: Using the Agent

```
User: Use the LLMProxy to help me setup Azure OpenAI

Agent: I'll help you configure Azure OpenAI for the LLM Proxy Service. 
       Let me start the interactive configuration wizard for you...

[Configuration wizard runs]

The LLM Proxy is now running with Azure OpenAI!
- PID: 12345
- Log: .claude/services/llm-proxy/logs/llm_proxy_20240124_143022.log
- Monitor: tail -f .claude/services/llm-proxy/logs/llm_proxy_20240124_143022.log
```

### Example 3: Running with Time Limit

```
User: Run the LLM proxy until 7pm when my Claude usage resets

Agent: I'll configure the LLM Proxy to run until 7:00 PM with automatic shutdown.

Would you like to schedule automatic shutdown? [y/N]: y

⏰ Schedule Configuration
  1. Run until specific time (e.g., 7:00 PM)
  2. Run for duration (e.g., 2 hours)
  3. Run until tomorrow at specific time

➤ Select: 1
📅 Enter shutdown time: 19:00
✅ Service will run until 07:00 PM (4 hours and 30 minutes)

Service started with scheduled shutdown:
⏰ Auto-stop at: 07:00 PM
📊 Monitor: tail -f logs/llm_proxy_20240124_143022.log
🛑 Stop early: kill 12345
❌ Cancel timer: rm scheduler_12345.py
```

## Service Management

### Starting the Service

```bash
# Using configuration wizard (recommended)
python3 configure_proxy.py

# Manual start with existing configuration
python3 launch_proxy.py &

# Using the agent
/agent:llm-proxy-agent
Start the LLM Proxy service
```

### Monitoring the Service

```bash
# Check if running
ps -p $(cat llm_proxy.pid)

# View real-time logs
tail -f logs/llm_proxy_*.log

# View last 50 log entries
tail -n 50 logs/llm_proxy_*.log
```

### Stopping the Service

```bash
# Using PID file
kill $(cat llm_proxy.pid)

# Manual stop
ps aux | grep llm_proxy
kill <PID>
```

### Scheduled Service Management

The LLM Proxy supports automatic shutdown scheduling, perfect for:
- Working around API rate limits that reset at specific times
- Cost management by limiting usage hours
- Testing with time boundaries
- Compliance with usage policies

**Scheduling Options:**
```bash
# Run until 7:00 PM today
Time: 19:00 or 7:00 PM

# Run for 2 hours
Duration: 2h or 120m

# Run until 9:00 AM tomorrow
Tomorrow time: 09:00 or 9:00 AM
```

**Managing Scheduled Services:**
```bash
# Check remaining time (look for SCHEDULER entries in log)
tail -f logs/llm_proxy_*.log | grep SCHEDULER

# Cancel scheduled shutdown
rm scheduler_<PID>.py

# Stop service immediately (ignores schedule)
kill <PID>
```

## Configuration Files

### .env File
Contains sensitive credentials and service settings:
```env
# Provider Credentials
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://...

# Service Configuration  
LLM_PROXY_PORT=8080
LLM_PROXY_LOG_LEVEL=INFO
LLM_PROXY_CACHE_SIZE=1000
```

### Provider JSON Config
Stores provider-specific settings:
```json
{
  "provider": "azure_openai",
  "name": "Azure OpenAI",
  "api_version": "2024-02-15-preview",
  "deployment_name": "gpt-4",
  "cache_enabled": true,
  "rate_limit": 60,
  "max_retries": 3
}
```

## Troubleshooting

### Service Won't Start
- Check API keys are correct
- Verify network connectivity
- Check logs for specific errors
- Ensure port 8080 is available

### Configuration Test Fails
- Verify API credentials
- Check provider endpoints
- Ensure required models are deployed
- Review provider-specific requirements

### Missing Dependencies
The configuration wizard will automatically install required dependencies:
- `python-dotenv` for environment management
- Provider SDKs as needed

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables** for production
3. **Rotate API keys regularly**
4. **Monitor usage through logs**
5. **Set appropriate rate limits**

## Advanced Configuration

### Multiple Providers
Configure multiple providers for load balancing:
```bash
python3 configure_proxy.py
# Select option 0 for multiple providers
# Configure each provider sequentially
```

### Custom Load Balancing
Edit `launch_proxy.py` to customize:
- `LoadBalanceStrategy.ROUND_ROBIN`
- `LoadBalanceStrategy.LEAST_LOADED`
- `LoadBalanceStrategy.COST_OPTIMIZED`
- `LoadBalanceStrategy.FASTEST_RESPONSE`

### Cache Configuration
Adjust in `.env`:
- `LLM_PROXY_CACHE_SIZE`: Number of cached responses
- `LLM_PROXY_CACHE_TTL`: Time-to-live in seconds

## API Usage

Once running, use the service in your code:

```python
from llm_proxy_service import get_llm_service

# Get service instance
llm = await get_llm_service()

# Make completion request
response = await llm.generate_completion(
    prompt="Hello, world!",
    model="gpt-4"
)
```

## Support

For issues or questions:
1. Check the logs first: `tail -f logs/llm_proxy_*.log`
2. Run configuration test: `python3 configure_proxy.py` (select test option)
3. Use the agent for guided troubleshooting: `/agent:llm-proxy-agent`