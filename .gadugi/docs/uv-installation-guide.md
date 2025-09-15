# UV Installation Guide for Gadugi

This guide provides comprehensive instructions for installing UV (Ultraviolet) - the fast Python package installer and dependency manager used by the Gadugi project.

## What is UV?

UV is a Rust-based Python packaging tool that provides:
- **10-100x faster** package installation than pip
- **Built-in virtual environment management**
- **Reproducible builds** with automatic lock file generation
- **Cross-platform compatibility** with single binary distribution
- **Drop-in pip replacement** for easy migration

## Installation Methods

### macOS and Linux (Recommended)

**Using the official installer:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using Homebrew (macOS):**
```bash
brew install uv
```

**Using pip (if you have Python already):**
```bash
pip install uv
```

### Windows

**Using PowerShell:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip:**
```bash
pip install uv
```

**Using Chocolatey:**
```bash
choco install uv
```

### Verify Installation

After installation, verify UV is working:
```bash
uv --version
```

You should see output similar to:
```
uv 0.6.9 (3d9460278 2025-03-20)
```

## Quick Start for Gadugi Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rysweet/gadugi.git
   cd gadugi
   ```

2. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

3. **Activate the environment:**
   ```bash
   # UV automatically manages the virtual environment
   # Use 'uv run' to execute commands in the environment
   ```

4. **Run tests:**
   ```bash
   uv run pytest tests/ -v
   ```

5. **Start development:**
   ```bash
   uv run python -m gadugi --help
   ```

## Key Differences from pip

| Feature | pip | UV |
|---------|-----|-----|
| Speed | Standard | 10-100x faster |
| Lock files | Manual (pip freeze) | Automatic (uv.lock) |
| Virtual envs | Manual (venv) | Built-in management |
| Dependency resolution | Basic | Advanced conflict resolution |
| Cross-platform | Good | Excellent |
| Memory usage | Higher | Lower |

## Environment Variables

UV supports several environment variables for configuration:

- `UV_CACHE_DIR`: Custom cache directory location
- `UV_NO_CACHE`: Disable caching (set to 1)
- `UV_INDEX_URL`: Custom PyPI index URL
- `UV_EXTRA_INDEX_URL`: Additional package indices

## Troubleshooting

### Common Issues

**1. Command not found after installation**
```bash
# Add UV to your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**2. SSL/TLS certificate errors**
```bash
# Use system certificates
uv install --trusted-host pypi.org --trusted-host pypi.python.org
```

**3. Corporate firewall issues**
```bash
# Configure proxy
uv install --proxy http://proxy.company.com:8080
```

**4. Permission errors on Windows**
```bash
# Run as administrator or use user installation
uv install --user
```

### Performance Issues

**Clear cache if experiencing issues:**
```bash
uv cache clean
```

**Recreate virtual environment:**
```bash
uv venv --force
uv sync
```

### Getting Help

- **UV Documentation**: https://github.com/astral-sh/uv
- **UV Issues**: https://github.com/astral-sh/uv/issues
- **Gadugi Specific Issues**: https://github.com/rysweet/gadugi/issues

## Advanced Configuration

### Custom Python Versions

UV can manage multiple Python versions:
```bash
# Install specific Python version
uv python install 3.11

# Use specific Python version
uv venv --python 3.11

# List available Python versions
uv python list
```

### Custom Configuration

Create `.uvrc` in your home directory for global settings:
```toml
[install]
index-url = "https://pypi.org/simple"
extra-index-url = ["https://test.pypi.org/simple"]

[cache]
dir = "~/.cache/uv"
```

### CI/CD Integration

For GitHub Actions, use the official UV action:
```yaml
- name: Install UV
  uses: astral-sh/setup-uv@v4
  with:
    version: "latest"

- name: Install dependencies
  run: uv sync --all-extras
```

## Migration from pip

If you're migrating from a pip-based workflow:

1. **Convert requirements.txt to pyproject.toml** (already done for Gadugi)
2. **Install UV** using the methods above
3. **Run `uv sync`** instead of `pip install -r requirements.txt`
4. **Use `uv run`** instead of activating virtual environments
5. **Use `uv add package`** instead of `pip install package`

## Next Steps

- See [UV Migration Guide](uv-migration-guide.md) for team transition instructions
- Check [UV Cheat Sheet](uv-cheat-sheet.md) for common commands
- Review the [Developer Setup](../README.md#development-setup) in the main README
