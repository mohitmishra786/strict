import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from strict.config import get_settings
from strict.core.math_ops import MathEngine
from strict.core.signal_engine import SignalEngine
from strict.integrity.schemas import SignalData

app = typer.Typer(
    name="strict",
    help="High-Integrity Signal Processing Engine with Diamond Gate Protocol",
    add_completion=False,
)

console = Console()


@app.command()
def version() -> None:
    """Show version information."""
    rprint("[bold cyan]Strict[/bold cyan] - High-Integrity Signal Processing Engine")
    rprint("Version: 0.1.0")
    rprint("Diamond Gate Protocol: Parse, Don't Validate + Correctness by Construction")


@app.command()
def validate(
    data: str = typer.Argument(..., help="Signal data as JSON or CSV"),
    format_type: str = typer.Option(
        "json", "--format", "-f", help="Input format (json, csv)"
    ),
) -> None:
    """Validate signal data."""
    try:
        if format_type == "json":
            signal_data = SignalData.model_validate_json(data)
        elif format_type == "csv":
            from strict.integrity.io import InputValidator

            parsed = InputValidator.parse_csv(data)
            if not parsed:
                rprint("[red]✗[/red] No data found in CSV")
                raise typer.Exit(1)

            # Collect all values from all rows
            values = [float(row.get("value", 0)) for row in parsed]
            # Use sample_rate from first row (or default to 1000)
            sample_rate = float(parsed[0].get("sample_rate", 1000))

            signal_data = SignalData(values=values, sample_rate=sample_rate)
        else:
            rprint(f"[red]✗[/red] Unsupported format: {format_type}")
            raise typer.Exit(1)

        result = signal_data.validate()
        if result.is_valid:
            rprint("[green]✓[/green] Signal data is valid")
            rprint(f"  Samples: {len(signal_data.values)}")
            rprint(f"  Sample Rate: {signal_data.sample_rate} Hz")
        else:
            rprint("[red]✗[/red] Signal data validation failed:")
            for error in result.errors:
                rprint(f"  - {error}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]✗[/red] Validation error: {e}")
        raise typer.Exit(1)


@app.command()
def compute(
    operation: str = typer.Argument(..., help="Operation to perform"),
    values: list[float] = typer.Argument(..., help="Numeric values"),
) -> None:
    """Perform mathematical operations."""
    engine = MathEngine()

    ops = {
        "mean": engine.mean,
        "median": engine.median,
        "std": engine.std,
        "variance": engine.variance,
        "min": engine.min,
        "max": engine.max,
        "sum": engine.sum,
        "product": engine.product,
        "add": lambda v: engine.add(v),
        "subtract": lambda v: engine.subtract(v),
        "multiply": lambda v: engine.multiply(v),
        "divide": lambda v: engine.divide(v),
    }

    if operation not in ops:
        rprint(f"[red]✗[/red] Unknown operation: {operation}")
        rprint(f"Available operations: {', '.join(ops.keys())}")
        raise typer.Exit(1)

    try:
        result = ops[operation](values)
        rprint(f"[green]✓[/green] [bold]{operation}[/bold]: {result}")
    except (ValueError, ZeroDivisionError) as e:
        rprint(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@app.command()
def fft(
    input_file: Path = typer.Argument(
        ..., exists=True, help="Input file with signal data"
    ),
) -> None:
    """Perform Fast Fourier Transform on signal data."""
    try:
        data = json.loads(input_file.read_text())
        signal_data = SignalData.model_validate(data)

        engine = SignalEngine()
        result = engine.fft(signal_data)

        table = Table(title="FFT Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Input Samples", str(len(signal_data.values)))
        table.add_row("Output Samples", str(len(result.values)))
        table.add_row("Sample Rate", f"{signal_data.sample_rate} Hz")

        console.print(table)

        if len(result.values) <= 20:
            rprint("\n[bold]FFT Values:[/bold]")
            for i, val in enumerate(result.values[:10]):
                rprint(f"  {i}: {val:.6f}")

    except Exception as e:
        rprint(f"[red]✗[/red] FFT error: {e}")
        raise typer.Exit(1)


@app.command()
def filter_signal(
    input_file: Path = typer.Argument(
        ..., exists=True, help="Input file with signal data"
    ),
    filter_type: str = typer.Option(
        "lowpass", "--type", "-t", help="Filter type (lowpass, highpass, bandpass)"
    ),
    cutoff: float = typer.Option(
        100.0,
        "--cutoff",
        "-c",
        help="Cutoff frequency in Hz (or low cutoff for bandpass)",
    ),
    high_cutoff: float = typer.Option(
        200.0, "--high-cutoff", "-H", help="High cutoff frequency for bandpass"
    ),
    order: int = typer.Option(4, "--order", "-o", help="Filter order"),
) -> None:
    """Apply digital filter to signal data."""
    try:
        data = json.loads(input_file.read_text())
        signal_data = SignalData.model_validate(data)

        engine = SignalEngine()

        if filter_type == "lowpass":
            result = engine.lowpass_filter(signal_data, cutoff, order)
        elif filter_type == "highpass":
            result = engine.highpass_filter(signal_data, cutoff, order)
        elif filter_type == "bandpass":
            result = engine.bandpass_filter(signal_data, cutoff, high_cutoff, order)
        else:
            rprint(f"[red]✗[/red] Unknown filter type: {filter_type}")
            raise typer.Exit(1)

        rprint(f"[green]✓[/green] Applied [bold]{filter_type}[/bold] filter")
        rprint(f"  Cutoff: {cutoff} Hz")
        rprint(f"  Order: {order}")
        rprint(f"  Output samples: {len(result.values)}")

    except Exception as e:
        rprint(f"[red]✗[/red] Filter error: {e}")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    try:
        settings = get_settings()

        table = Table(title="Strict Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        config_dict = {
            "Debug": settings.debug,
            "Log Level": settings.log_level,
            "OpenAI API Key": "***" if settings.openai_api_key else "(not set)",
            "Ollama Base URL": str(settings.ollama_base_url),
            "Database URL": "***" if settings.database_url else "(not set)",
            "Redis URL": "***" if settings.redis_url else "(not set)",
            "S3 Bucket": settings.s3_bucket_name or "(not set)",
            "Secret Key": "***" if settings.secret_key else "(not set)",
        }

        for key, value in config_dict.items():
            table.add_row(key, str(value))

        console.print(table)

    except Exception as e:
        rprint(f"[red]✗[/red] Config error: {e}")
        raise typer.Exit(1)


@app.command()
def server(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start the API server."""
    rprint(f"[bold cyan]Starting Strict API server[/bold cyan]")
    rprint(f"  Host: {host}")
    rprint(f"  Port: {port}")
    rprint(f"  Reload: {reload}")
    rprint(f"\n[yellow]Press Ctrl+C to stop[/yellow]")

    import uvicorn

    uvicorn.run(
        "strict.api:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
