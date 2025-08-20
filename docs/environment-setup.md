# Environment Configuration Guide

This guide explains how to configure environment variables for Gadugi services.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   # Edit the file with your preferred editor
   nano .env
   # or
   vim .env
   ```

3. Set your Neo4j password and other required values.

## Required Environment Variables

### Neo4j Database

- `NEO4J_PASSWORD` - **Required**: Password for Neo4j database
- `NEO4J_USER` - Username for Neo4j (default: `neo4j`)
- `NEO4J_URI` - Connection URI (default: `bolt://localhost:7688`)
- `NEO4J_HTTP_PORT` - HTTP port (default: `7475`)
- `NEO4J_BOLT_PORT` - Bolt protocol port (default: `7688`)

### Claude API

- `CLAUDE_API_KEY` - **Required for orchestrator**: Your Claude API key

### Environment Type

- `ENVIRONMENT` - Set to `development`, `staging`, or `production`
  - In `production`, stricter security checks are enforced
  - Password requirements are mandatory in production

## Docker Compose Usage

The `docker-compose.yml` file automatically reads from your `.env` file:

```bash
# Start services with environment variables
docker-compose up -d

# Verify Neo4j is running with your configuration
docker-compose ps
docker-compose logs neo4j
```

## Python Client Usage

The Neo4j Python client automatically reads environment variables:

```python
from neo4j_client import Neo4jClient

# Client automatically uses environment variables
client = Neo4jClient.from_environment()

# Or override specific values
client = Neo4jClient(
    uri="bolt://custom-host:7687",
    password=os.getenv("CUSTOM_PASSWORD")
)
```

## Security Best Practices

1. **Never commit `.env` files to version control**
   - The `.gitignore` file already excludes `.env`
   - Only commit `.env.example` with placeholder values

2. **Use strong passwords in production**
   - Generate secure passwords: `openssl rand -base64 32`  # pragma: allowlist secret
   - Store production secrets in a secure vault service

3. **Rotate credentials regularly**
   - Update passwords periodically
   - Use different passwords for each environment

4. **Environment-specific files**
   - Use `.env.development` for local development
   - Use `.env.production` for production (never commit)
   - Load the appropriate file based on your environment

## Troubleshooting

### Neo4j connection fails

1. Check if Neo4j is running:
   ```bash
   docker-compose ps
   ```

2. Verify environment variables are loaded:
   ```bash
   docker-compose config
   ```

3. Test connection with the client:
   ```python
   python neo4j_client/client.py
   ```

### Missing environment variables

If you see errors about missing environment variables:

1. Ensure `.env` file exists and is readable
2. Check variable names match exactly (case-sensitive)
3. For Docker Compose, ensure you're in the right directory
4. Try sourcing the file manually: `source .env`

### Production deployment

For production deployments:

1. Use environment-specific secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
2. Set `ENVIRONMENT=production` to enforce strict security
3. Never use default or development passwords
4. Enable SSL/TLS for Neo4j connections
