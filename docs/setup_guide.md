# Setup Guide

This guide covers the installation and configuration of Vaak.

---

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mohitmishra786/vaak.git
cd vaak
```

### 2. Create Virtual Environment

Create a virtual environment named `bhasha`:

```bash
python -m venv bhasha
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

Edit `.env.local` with your configuration:

```ini
# Security - REQUIRED
VAAK_SECRET_KEY=your-secret-key-here

# Runtime (optional, defaults shown)
VAAK_DEBUG=false
VAAK_LOG_LEVEL=INFO

# Processing (optional)
VAAK_MAX_RETRIES=3
VAAK_TIMEOUT_SECONDS=30.0

# Processor Configuration
VAAK_CLOUD_ENDPOINT=https://api.openai.com/v1
VAAK_LOCAL_MODEL_PATH=/path/to/local/model
VAAK_TOKEN_THRESHOLD=500

# Failover Configuration
VAAK_ENABLE_FAILOVER=true
VAAK_CLOUD_FAILURE_PROBABILITY=0.01
VAAK_LOCAL_FAILURE_PROBABILITY=0.05
```

---

## Verification

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/vaak/
```

### Import Test

```python
from vaak.integrity import SignalConfig, ProcessingRequest
from vaak.core import validate_model_output, calculate_system_success_probability
from vaak.config import settings

print(f"Vaak loaded successfully. Debug mode: {settings.debug}")
```

---

## Project Structure

```
vaak/
    docs/               Documentation
    src/vaak/           Source code
        config.py       Configuration
        core/           Math engine (pure functions)
        integrity/      Pydantic models (The Gatekeeper)
    tests/              Test suite
```

---

## Development Workflow

1. Make changes to source files
2. Run tests: `pytest tests/ -v`
3. Check types: `mypy src/vaak/`
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

Check that all required fields are provided and match the expected types. Vaak uses strict mode, so type coercion is disabled.

### Environment Variable Issues

Verify the `.env` file exists and contains valid values. Variables must use the `VAAK_` prefix.
