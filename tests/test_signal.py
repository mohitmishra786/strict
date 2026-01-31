import pytest
import numpy as np
from strict.core.signal_engine import SignalEngine
from strict.integrity.schemas import SignalConfig, SignalType


def test_generate_signal():
    config = SignalConfig(
        signal_type=SignalType.ANALOG,
        sampling_rate=100.0,
        frequency=10.0,
        amplitude=0.5,
        duration=1.0,
    )
    sig = SignalEngine.generate_signal(config)
    assert len(sig) == 100
    assert np.max(sig) <= 0.5 + 1e-9


def test_fft():
    # Simple sine wave
    fs = 100.0
    t = np.linspace(0, 1.0, 100, endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * 10.0 * t)

    freq, mag = SignalEngine.compute_fft(sig, fs)

    # Peak should be at 10Hz
    peak_idx = np.argmax(mag)
    peak_freq = freq[peak_idx]
    assert abs(peak_freq - 10.0) < 1.0


def test_lowpass_filter():
    fs = 100.0
    t = np.linspace(0, 1.0, 100, endpoint=False)
    # 10Hz signal + 40Hz noise
    sig = np.sin(2 * np.pi * 10.0 * t) + 0.5 * np.sin(2 * np.pi * 40.0 * t)

    filtered = SignalEngine.apply_lowpass_filter(sig, cutoff=20.0, fs=fs)

    # Check if 40Hz is attenuated (simple check: reduced variance)
    # Or check FFT of filtered
    freq, mag = SignalEngine.compute_fft(filtered, fs)
    idx_40 = np.argmin(np.abs(freq - 40.0))
    idx_10 = np.argmin(np.abs(freq - 10.0))

    assert mag[idx_40] < 0.1  # Noise attenuated
    assert mag[idx_10] > 0.4  # Signal preserved
