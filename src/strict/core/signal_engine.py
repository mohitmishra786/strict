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
