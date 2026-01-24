# Strict

Strict implements the **Diamond Gate Protocol**, a strict four-layer architecture designed around the principle of **"Correctness by Construction"**.

---

## Philosophy

**"Parse, Don't Validate"**: We do not check data after ingestion; we parse it into strictly-typed structures at the very edge. If data cannot form a valid Model, it is rejected immediately.

**No invalid state is ever representable in the Core layer.**

---

## Architecture

```
Layer 1: Dirty Edge      Raw input (dict, JSON, env vars)
        |
        v
Layer 2: Integrity       Pydantic V2 validation (The Gatekeeper)
        |
        v
Layer 3: Core            Pure mathematical functions
        |
        v
Layer 4: Output          Validated output schema
```

See [docs/architecture.md](docs/architecture.md) for detailed documentation with Mermaid diagrams.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/mohitmishra786/rough.git
cd rough

# Create virtual environment (named bhasha)
python3.11 -m venv bhasha
source bhasha/bin/activate

# Install
pip install -e .
```

---

## Quick Start

```python
from rough.integrity import SignalConfig, ProcessingRequest
from rough.core import validate_model_output, calculate_system_success_probability

# Create a validated signal configuration
config = SignalConfig(
    signal_type="analog",
    sampling_rate=44100.0,
    frequency=440.0,
    amplitude=0.5,
    duration=1.0,
)

# Calculate system reliability with failover
p_success = calculate_system_success_probability(
    cloud_failure_probability=0.01,
    local_failure_probability=0.05,
)
print(f"System success probability: {p_success:.4f}")  # 0.9995
```

---

## Configuration

Copy `.env` to `.env.local` and configure:

```ini
STRICT_SECRET_KEY=your-secret-key
STRICT_DEBUG=false
STRICT_LOG_LEVEL=INFO
```

See [docs/setup_guide.md](docs/setup_guide.md) for full configuration options.

---

## Documentation

- [Architecture Overview](docs/architecture.md) - Diamond Gate Protocol and layer design
- [Mathematical Proofs](docs/mathematical_proofs.md) - LaTeX formulas and derivations
- [Setup Guide](docs/setup_guide.md) - Installation and configuration

---

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/rough/

# Linting
ruff check src/ tests/

# Formatting
ruff format src/ tests/
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
