# Setup Guide

This guide covers the installation and configuration of Rough.

---

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mohitmishra786/rough.git
cd rough
```

### 2. Create Virtual Environment

Create a virtual environment named `bhasha`:

```bash
python3.11 -m venv bhasha
```

### 3. Activate Virtual Environment

On macOS/Linux:
```bash
source bhasha/bin/activate
```

On Windows:
```powershell
.\bhasha\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -e .
```

For development dependencies:
```bash
pip install -e ".[dev]"
```

---

## Configuration

### Environment Variables

Copy the `.env` template and fill in your values:

```bash
cp .env .env.local
```

# Security - REQUIRED
STRICT_SECRET_KEY=your-secret-key-here

# Runtime (optional, defaults shown)
STRICT_DEBUG=false
STRICT_LOG_LEVEL=INFO

# Processing (optional)
STRICT_MAX_RETRIES=3
STRICT_TIMEOUT_SECONDS=30.0

# Processor Configuration
STRICT_CLOUD_ENDPOINT=https://api.openai.com/v1
STRICT_LOCAL_MODEL_PATH=/path/to/local/model
STRICT_TOKEN_THRESHOLD=500

# Failover Configuration
STRICT_ENABLE_FAILOVER=true
STRICT_CLOUD_FAILURE_PROBABILITY=0.01
STRICT_LOCAL_FAILURE_PROBABILITY=0.05
```

---

## Verification

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/rough/
```

### Import Test

```python
from rough.integrity import SignalConfig, ProcessingRequest
from rough.core import validate_model_output, calculate_system_success_probability
from rough.config import settings

print(f"Rough loaded successfully. Debug mode: {settings.debug}")
```

---

## Project Structure

```
rough/
    docs/               Documentation
    src/rough/           Source code
        config.py       Configuration
        core/           Math engine (pure functions)
        integrity/      Pydantic models (The Gatekeeper)
    tests/              Test suite
```

---

## Development Workflow

1. Make changes to source files
2. Run tests: `pytest tests/ -v`
3. Check types: `mypy src/rough/`
4. Format code: `ruff format src/ tests/`
5. Lint code: `ruff check src/ tests/`

---

## Troubleshooting

### Import Errors

Ensure the package is installed in editable mode:
```bash
pip install -e .
```

### Pydantic Validation Errors

Check that all required fields are provided and match the expected types. Rough uses strict mode, so type coercion is disabled.

### Environment Variable Issues

Verify the `.env` file exists and contains valid values. Variables must use the `STRICT_` prefix.
