from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import scipy.signal as signal

from strict.integrity.schemas import SignalData

if TYPE_CHECKING:
    from numpy.typing import NDArray


class SignalEngine:
    """Signal Processing Engine using SciPy."""

    def __init__(self) -> None:
        """Initialize the SignalEngine."""
        pass

    @staticmethod
    def generate_signal(config: SignalConfig) -> list[float]:
        """Generate a signal based on configuration.

        Args:
            config: Signal configuration.

        Returns:
            Generated signal sample values.
        """
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
        """Compute FFT magnitude and frequency bins.

        Args:
            values: Signal values.
            sample_rate: Sampling rate in Hz.

        Returns:
            Tuple of (frequencies, magnitudes).
        """
        data = np.array(values)
        n = len(data)
        freq = np.fft.rfftfreq(n, d=1 / sample_rate)
        mag = np.abs(np.fft.rfft(data)) / n
        return freq, mag

    @staticmethod
    def apply_lowpass_filter(
        values: list[float] | NDArray, cutoff: float, fs: float, order: int = 5
    ) -> list[float]:
        """Apply lowpass filter to raw values.

        Args:
            values: Signal values.
            cutoff: Cutoff frequency in Hz.
            fs: Sampling rate in Hz.
            order: Filter order.

        Returns:
            Filtered values as list.
        """
        data = np.array(values)
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="low", analog=False)
        y = signal.lfilter(b, a, data)
        return y.tolist()

    @staticmethod
    def fft(signal_data: SignalData) -> SignalData:
        """Compute FFT of the signal data.

        Args:
            signal_data: Input signal data.

        Returns:
            New SignalData with FFT magnitude values.
        """
        data = np.array(signal_data.values)
        n = len(data)
        magnitude = np.abs(np.fft.rfft(data)) / n

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
        """Apply Butterworth lowpass filter.

        Args:
            signal_data: Input signal data.
            cutoff: Cutoff frequency in Hz.
            order: Filter order (default: 5).

        Returns:
            New SignalData with filtered values.
        """
        data = np.array(signal_data.values)
        nyquist = 0.5 * signal_data.sample_rate
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="low", analog=False)
        y = signal.lfilter(b, a, data)

        return SignalData(
            values=y.tolist(),
            sample_rate=signal_data.sample_rate,
        )

    @staticmethod
    def highpass_filter(
        signal_data: SignalData,
        cutoff: float,
        order: int = 5,
    ) -> SignalData:
        """Apply Butterworth highpass filter.

        Args:
            signal_data: Input signal data.
            cutoff: Cutoff frequency in Hz.
            order: Filter order (default: 5).

        Returns:
            New SignalData with filtered values.
        """
        data = np.array(signal_data.values)
        nyquist = 0.5 * signal_data.sample_rate
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
        """Apply Butterworth bandpass filter.

        Args:
            signal_data: Input signal data.
            low: Low cutoff frequency in Hz.
            high: High cutoff frequency in Hz.
            order: Filter order (default: 5).

        Returns:
            New SignalData with filtered values.
        """
        data = np.array(signal_data.values)
        nyquist = 0.5 * signal_data.sample_rate
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
        """Compute basic statistics for signal data.

        Args:
            signal_data: Input signal data.

        Returns:
            Dictionary with mean, std, min, max.
        """
        data = np.array(signal_data.values)
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
        }
