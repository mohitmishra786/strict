import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from strict.cli import app

runner = CliRunner()

SAMPLE_SIGNAL_DATA = {
    "values": [1.0, 2.0, 3.0, 4.0, 5.0],
    "sample_rate": 1000.0,
}


@pytest.fixture
def temp_signal_file(tmp_path: Path) -> Path:
    """Create a temporary file with signal data."""
    file_path = tmp_path / "signal.json"
    file_path.write_text(json.dumps(SAMPLE_SIGNAL_DATA))
    return file_path


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Strict" in result.stdout
    assert "0.1.0" in result.stdout
    assert "Diamond Gate Protocol" in result.stdout


def test_validate_json():
    """Test validation with JSON format."""
    data = json.dumps(SAMPLE_SIGNAL_DATA)
    result = runner.invoke(app, ["validate", data, "--format", "json"])
    assert result.exit_code == 0
    assert "✓" in result.stdout or "valid" in result.stdout.lower()


def test_validate_csv():
    """Test validation with CSV format."""
    csv_data = "value,sample_rate\n1.0,1000\n2.0,1000\n"
    result = runner.invoke(app, ["validate", csv_data, "--format", "csv"])
    assert result.exit_code == 0
    assert "✓" in result.stdout or "valid" in result.stdout.lower()


def test_validate_invalid_json():
    """Test validation with invalid JSON."""
    result = runner.invoke(app, ["validate", "invalid json", "--format", "json"])
    assert result.exit_code == 1


def test_compute_mean():
    """Test mean computation."""
    result = runner.invoke(app, ["compute", "mean", "1", "2", "3", "4", "5"])
    assert result.exit_code == 0
    assert "3.0" in result.stdout


def test_compute_sum():
    """Test sum computation."""
    result = runner.invoke(app, ["compute", "sum", "1", "2", "3"])
    assert result.exit_code == 0
    assert "6.0" in result.stdout


def test_compute_std():
    """Test standard deviation computation."""
    result = runner.invoke(
        app, ["compute", "std", "2", "4", "4", "4", "5", "5", "7", "9"]
    )
    assert result.exit_code == 0


def test_compute_invalid_operation():
    """Test invalid operation."""
    result = runner.invoke(app, ["compute", "invalid_op", "1", "2", "3"])
    assert result.exit_code == 1
    assert "Unknown operation" in result.stdout


def test_fft(temp_signal_file: Path):
    """Test FFT command."""
    result = runner.invoke(app, ["fft", str(temp_signal_file)])
    assert result.exit_code == 0
    assert "FFT Results" in result.stdout


def test_filter_lowpass(temp_signal_file: Path):
    """Test lowpass filter command."""
    result = runner.invoke(
        app,
        [
            "filter-signal",
            str(temp_signal_file),
            "--type",
            "lowpass",
            "--cutoff",
            "100",
            "--order",
            "4",
        ],
    )
    assert result.exit_code == 0
    assert "lowpass" in result.stdout


def test_filter_highpass(temp_signal_file: Path):
    """Test highpass filter command."""
    result = runner.invoke(
        app,
        [
            "filter-signal",
            str(temp_signal_file),
            "--type",
            "highpass",
            "--cutoff",
            "50",
            "--order",
            "4",
        ],
    )
    assert result.exit_code == 0
    assert "highpass" in result.stdout


def test_filter_invalid_type(temp_signal_file: Path):
    """Test filter with invalid type."""
    result = runner.invoke(
        app,
        ["filter-signal", str(temp_signal_file), "--type", "invalid"],
    )
    assert result.exit_code == 1


def test_config():
    """Test config command."""
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Configuration" in result.stdout or "Environment" in result.stdout


def test_compute_division_by_zero():
    """Test division by zero handling."""
    result = runner.invoke(app, ["compute", "divide", "1", "0"])
    assert result.exit_code == 1
