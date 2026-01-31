"""Math Engine - High-level interface for mathematical operations.

This module provides a class-based interface for common mathematical operations,
wrapping the pure functions from math_engine module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class MathEngine:
    """High-level interface for mathematical operations.

    Provides convenient methods for statistical and mathematical operations
    on numeric data using NumPy for performance.
    """

    def __init__(self) -> None:
        """Initialize the MathEngine."""
        pass

    def mean(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the arithmetic mean of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The arithmetic mean.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate mean of empty list")
        arr = np.array(values)
        return float(np.mean(arr))

    def median(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the median of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The median value.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate median of empty list")
        arr = np.array(values)
        return float(np.median(arr))

    def std(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the standard deviation of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The standard deviation.

        Raises:
            ValueError: If values list has fewer than 2 elements.
        """
        if len(values) < 2:
            raise ValueError("Cannot calculate std with fewer than 2 values")
        arr = np.array(values)
        return float(np.std(arr, ddof=1))

    def variance(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the variance of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The variance.

        Raises:
            ValueError: If values list has fewer than 2 elements.
        """
        if len(values) < 2:
            raise ValueError("Cannot calculate variance with fewer than 2 values")
        arr = np.array(values)
        return float(np.var(arr, ddof=1))

    def min(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the minimum value.

        Args:
            values: List or array of numeric values.

        Returns:
            The minimum value.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate min of empty list")
        arr = np.array(values)
        return float(np.min(arr))

    def max(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the maximum value.

        Args:
            values: List or array of numeric values.

        Returns:
            The maximum value.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate max of empty list")
        arr = np.array(values)
        return float(np.max(arr))

    def sum(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the sum of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The sum.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate sum of empty list")
        arr = np.array(values)
        return float(np.sum(arr))

    def product(self, values: list[float] | NDArray[np.float64]) -> float:
        """Calculate the product of values.

        Args:
            values: List or array of numeric values.

        Returns:
            The product.

        Raises:
            ValueError: If values list is empty.
        """
        if len(values) == 0:
            raise ValueError("Cannot calculate product of empty list")
        result = 1.0
        for v in values:
            result *= v
        return float(result)

    def add(self, values: list[float] | NDArray[np.float64]) -> float:
        """Add all values together (alias for sum).

        Args:
            values: List or array of numeric values.

        Returns:
            The sum.
        """
        return self.sum(values)

    def subtract(self, values: list[float] | NDArray[np.float64]) -> float:
        """Subtract all values sequentially from left to right.

        Args:
            values: List or array of numeric values.

        Returns:
            The result of sequential subtraction.

        Raises:
            ValueError: If values list has fewer than 2 elements.
        """
        if len(values) < 2:
            raise ValueError("Subtract requires at least 2 values")
        result = values[0]
        for v in values[1:]:
            result -= v
        return float(result)

    def multiply(self, values: list[float] | NDArray[np.float64]) -> float:
        """Multiply all values together.

        Args:
            values: List or array of numeric values.

        Returns:
            The product.
        """
        return self.product(values)

    def divide(self, values: list[float] | NDArray[np.float64]) -> float:
        """Divide all values sequentially from left to right.

        Args:
            values: List or array of numeric values.

        Returns:
            The result of sequential division.

        Raises:
            ValueError: If values list has fewer than 2 elements.
            ZeroDivisionError: If any division by zero occurs.
        """
        if len(values) < 2:
            raise ValueError("Divide requires at least 2 values")
        result = values[0]
        for v in values[1:]:
            if v == 0:
                raise ZeroDivisionError("Division by zero")
            result /= v
        return float(result)
