import numpy as np
import scipy.signal as signal
from strict.integrity.schemas import SignalConfig


class SignalEngine:
    """Signal Processing Engine using SciPy."""

    @staticmethod
    def generate_signal(config: SignalConfig) -> np.ndarray:
        """Generate a simulated signal based on config."""
        t = np.linspace(
            0,
            config.duration,
            int(config.sampling_rate * config.duration),
            endpoint=False,
        )
        # Simple sine wave for demo
        sig = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
        return sig

    @staticmethod
    def compute_fft(
        data: np.ndarray, sampling_rate: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute FFT of the signal."""
        n = len(data)
        freq = np.fft.rfftfreq(n, d=1 / sampling_rate)
        magnitude = np.abs(np.fft.rfft(data)) / n
        return freq, magnitude

    @staticmethod
    def apply_lowpass_filter(
        data: np.ndarray, cutoff: float, fs: float, order: int = 5
    ) -> np.ndarray:
        """Apply Butterworth lowpass filter."""
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="low", analog=False)
        y = signal.lfilter(b, a, data)
        return y
