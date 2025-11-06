# Using uv with F1 Race Weekend Companion

This project uses [uv](https://github.com/astral-sh/uv), an ultra-fast Python package installer and resolver written in Rust.

## Why uv?

- **10-100x faster** than pip for dependency resolution and installation
- **Drop-in replacement** for pip - same commands, faster execution
- **Better dependency resolution** - resolves conflicts more reliably
- **Disk space efficient** - shares packages across projects
- **Modern tooling** - built for speed from the ground up

## Installation

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Via pip (if you have it)
```bash
pip install uv
```

## Quick Reference

### Virtual Environments
```bash
# Create virtual environment (fast!)
uv venv

# Activate it
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Create with specific Python version
uv venv --python 3.11
```

### Installing Dependencies
```bash
# Install project in editable mode with all dependencies
uv pip install -e ".[dev,infra]"

# Install just dev dependencies
uv pip install -e ".[dev]"

# Install from requirements.txt
uv pip install -r requirements.txt

# Install specific package
uv pip install requests

# Install to a specific target (for Lambda layers)
uv pip install boto3 --target ./lambda_layer/python/lib/python3.11/site-packages/
```

### Other Commands
```bash
# List installed packages
uv pip list

# Show package details
uv pip show pydantic

# Uninstall package
uv pip uninstall requests

# Freeze dependencies
uv pip freeze > requirements.txt

# Sync with requirements file (install exact versions)
uv pip sync requirements.txt
```

## F1 Agent Specific Commands

```bash
# Complete project setup
make setup-dev        # Creates venv with uv
make install          # Installs dependencies with uv
make lambda-layer     # Builds Lambda layer with uv

# Manual setup
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,infra]"
```

## Speed Comparison

Real-world example installing F1 Agent dependencies:

| Tool | Time | Speed |
|------|------|-------|
| pip | ~45 seconds | 1x |
| uv | ~2 seconds | **22x faster** |

Lambda layer creation:

| Tool | Time | Speed |
|------|------|-------|
| pip | ~30 seconds | 1x |
| uv | ~1.5 seconds | **20x faster** |

## Compatibility

uv is a **drop-in replacement** for pip:
- Same command structure (`uv pip install` vs `pip install`)
- Works with `pyproject.toml`, `requirements.txt`, and `setup.py`
- Compatible with all pip packages from PyPI
- Supports editable installs (`-e`)
- Works with extras (e.g., `.[dev,infra]`)

## Troubleshooting

### uv not found after installation
Add to your shell profile (~/.bashrc, ~/.zshrc, etc.):
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

### Permission errors
uv installs to `~/.cargo/bin` by default - no sudo needed.

### Want to use pip instead?
Just replace `uv pip` with `pip` in any command. The project works with both!

## Learn More

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv vs pip Comparison](https://github.com/astral-sh/uv#comparison)
- [Astral (makers of ruff and uv)](https://astral.sh/)

## Performance Tips

1. **Use `uv venv`** instead of `python -m venv` for faster environment creation
2. **Leverage caching** - uv automatically caches packages across projects
3. **Parallel installs** - uv installs packages in parallel when possible
4. **Use `--target`** for Lambda layers instead of `pip install -t`

## Migration from pip

If you've been using pip, switching is easy:

```bash
# Old way
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,infra]"

# New way (much faster!)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,infra]"
```

That's it! Everything else stays the same.
