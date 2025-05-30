"""
In this file, we define the class for handling chat
the format_duration function is used to format a duration
 given in milliseconds to a human-readable string.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class TimeUnit(float, Enum):
    """Time units with their conversion factors to milliseconds."""

    MILLISECOND = 1.0
    SECOND = 1000.0
    MINUTE = 60.0 * 1000.0
    HOUR = 60.0 * 60.0 * 1000.0
    NANOSECOND = 1.0 / 1_000_000.0


@dataclass()
class Duration:
    """Represents a duration with a specific time unit."""

    value: int
    unit: TimeUnit

    def to_ms(self) -> float:
        """Convert the duration to milliseconds."""
        return self.value * self.unit.value


def convert_to_units(duration_ms: float) -> List[Duration]:
    """
    Convert a duration given in milliseconds to a list of units.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        List of Duration objects with the corresponding units
    """

    if not duration_ms:
        return [Duration(0, TimeUnit.MILLISECOND)]
    units = [TimeUnit.HOUR, TimeUnit.MINUTE, TimeUnit.SECOND, TimeUnit.MILLISECOND]
    results = []
    remaining_duration_ms = duration_ms

    for unit in units:
        if unit == TimeUnit.MILLISECOND:
            value = int(remaining_duration_ms)
        else:
            value = int(remaining_duration_ms // unit.value)
            remaining_duration_ms %= unit.value

        if value > 0:
            results.append(Duration(value, unit))

    return results if results else [Duration(0, TimeUnit.MILLISECOND)]


def format_unit(duration: Duration) -> str:
    """
    Format a single Duration object to string.

    Args:
        duration: Duration object to format

    Returns:
        Formatted string for the duration
    """
    unit_name = duration.unit.name.lower()
    if unit_name == "millisecond":
        unit_name = "ms"
    return f"{duration.value} {unit_name}{'s' if duration.value != 1 and unit_name != 'ms' else ''}"


def format_duration(value: float, source_unit: TimeUnit = TimeUnit.MILLISECOND) -> str:
    """
    Format a duration to a human-readable string.

    Args:
        value: Duration value
        source_unit: Source time unit (default: milliseconds)

    Returns:
        Formatted string in the format "X hours, Y minutes, Z seconds, W ms"
    """
    duration_ms = value * source_unit.value
    durations = convert_to_units(duration_ms)
    return ", ".join(format_unit(d) for d in durations)


def format_duration_ns(nanoseconds: float) -> str:
    """
    Format a duration given in nanoseconds to a human-readable string.

    Args:
        nanoseconds: Duration in nanoseconds

    Returns:
        Formatted string in the format "X hours, Y minutes, Z seconds, W ms"
    """
    return format_duration(nanoseconds, TimeUnit.NANOSECOND)


def format_duration_ms(milliseconds: float) -> str:
    """
    Format a duration given in milliseconds to a human-readable string.
    Maintained for backward compatibility.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted string in the format "X hours, Y minutes, Z seconds, W ms"
    """
    return format_duration(milliseconds, TimeUnit.MILLISECOND)
