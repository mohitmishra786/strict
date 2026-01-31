from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
import scipy.signal as signal

from strict.integrity.schemas import SignalData, SignalConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


class SignalEngine:
    """Signal Processing Engine using SciPy."""

    def __init__(self) -> None:
        """Initialize the SignalEngine."""
        pass

    @staticmethod
    def generate_signal(config: SignalConfig) -> list[float]:
        """Generate a signal based on configuration."""
        t = np.linspace(
            0,
            config.duration,
            int(config.duration * config.sampling_rate),
            endpoint=False,
        )
        values = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
        return values.tolist()

    @staticmethod
    def compute_fft(
        values: list[float] | NDArray, sample_rate: float
    ) -> tuple[NDArray, NDArray]:
        """Compute FFT magnitude and frequency bins."""
        data = np.array(values)
        n = len(data)
        if n == 0:
            return np.array([]), np.array([])

        freq = np.fft.rfftfreq(n, d=1 / sample_rate)
        mag = np.abs(np.fft.rfft(data)) / n
        return freq, mag

    @staticmethod
    def _validate_filter_params(
        values: list[float] | NDArray,
        cutoff: float | list[float],
        fs: float,
        order: int,
    ) -> float:
        """Validate common filter parameters."""
        if fs <= 0:
            raise ValueError("Sampling rate (fs) must be positive")
        if len(values) == 0:
            raise ValueError("Input values cannot be empty")
        if order <= 0:
            raise ValueError("Filter order must be a positive integer")

        nyquist = 0.5 * fs
        if isinstance(cutoff, list):
            for c in cutoff:
                if c <= 0 or c >= nyquist:
                    raise ValueError(
                        f"Cutoff frequency {c} must be between 0 and {nyquist}"
                    )
        else:
            if cutoff <= 0 or cutoff >= nyquist:
                raise ValueError(
                    f"Cutoff frequency {cutoff} must be between 0 and {nyquist}"
                )

        return nyquist

    @staticmethod
    def apply_lowpass_filter(
        values: list[float] | NDArray, cutoff: float, fs: float, order: int = 5
    ) -> list[float]:
        """Apply lowpass filter to raw values."""
        nyquist = SignalEngine._validate_filter_params(values, cutoff, fs, order)
        data = np.array(values)
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="low", analog=False)
        y = signal.lfilter(b, a, data)
        return y.tolist()

    @staticmethod
    def fft(signal_data: SignalData) -> SignalData:
        """Compute FFT of the signal data."""
        _, magnitude = SignalEngine.compute_fft(
            signal_data.values, signal_data.sample_rate
        )

        return SignalData(
            values=magnitude.tolist(),
            sample_rate=signal_data.sample_rate / 2,
        )

    @staticmethod
    def lowpass_filter(
        signal_data: SignalData,
        cutoff: float,
        order: int = 5,
    ) -> SignalData:
        """Apply Butterworth lowpass filter."""
        filtered = SignalEngine.apply_lowpass_filter(
            signal_data.values, cutoff, signal_data.sample_rate, order
        )
        return SignalData(
            values=filtered,
            sample_rate=signal_data.sample_rate,
        )

    @staticmethod
    def highpass_filter(
        signal_data: SignalData,
        cutoff: float,
        order: int = 5,
    ) -> SignalData:
        """Apply Butterworth highpass filter."""
        nyquist = SignalEngine._validate_filter_params(
            signal_data.values, cutoff, signal_data.sample_rate, order
        )
        data = np.array(signal_data.values)
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="high", analog=False)
        y = signal.lfilter(b, a, data)

        return SignalData(
            values=y.tolist(),
            sample_rate=signal_data.sample_rate,
        )

    @staticmethod
    def bandpass_filter(
        signal_data: SignalData,
        low: float,
        high: float,
        order: int = 5,
    ) -> SignalData:
        """Apply Butterworth bandpass filter."""
        nyquist = SignalEngine._validate_filter_params(
            signal_data.values, [low, high], signal_data.sample_rate, order
        )
        data = np.array(signal_data.values)
        low_normal = low / nyquist
        high_normal = high / nyquist
        b, a = signal.butter(
            order, [low_normal, high_normal], btype="band", analog=False
        )
        y = signal.lfilter(b, a, data)

        return SignalData(
            values=y.tolist(),
            sample_rate=signal_data.sample_rate,
        )

    @staticmethod
    def compute_statistics(
        signal_data: SignalData,
    ) -> dict[str, float]:
        """Compute basic statistics for signal data."""
        data = np.array(signal_data.values)
        if data.size == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
        }
