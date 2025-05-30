"""Unit tests for the format_duration module.

This module contains comprehensive unit tests for the duration formatting functionality,
focusing on various time units and formatting scenarios.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from apollo.service.tool.format import (
    format_duration_ns,
    format_duration_ms,
)


class TestFormatDuration(unittest.TestCase):
    """Test cases for duration formatting functions."""

    def test_format_duration_ns(self):
        """Test nanosecond duration formatting."""
        # Test various nanosecond values
        self.assertEqual(format_duration_ns(0), "0 ms")
        self.assertEqual(format_duration_ns(999), "0 ms")
        self.assertEqual(format_duration_ns(1000), "0 ms")
        self.assertEqual(format_duration_ns(1500), "0 ms")
        self.assertEqual(format_duration_ns(1000000), "1 ms")
        self.assertEqual(format_duration_ns(1000000000), "1 second")

    def test_format_duration_ms(self):
        """Test millisecond duration formatting."""
        # Test various millisecond values
        self.assertEqual(format_duration_ms(0), "0 ms")
        self.assertEqual(format_duration_ms(999), "999 ms")
        self.assertEqual(format_duration_ms(1000), "1 second")
        self.assertEqual(format_duration_ms(1500), "1 second, 500 ms")
        self.assertEqual(format_duration_ms(60000), "1 minute")
        self.assertEqual(format_duration_ms(3600000), "1 hour")

    def test_edge_cases(self):
        """Test edge cases for duration formatting."""
        # Test very small values
        self.assertEqual(format_duration_ns(1), "0 ms")
        self.assertEqual(format_duration_ms(1), "1 ms")

        # Test very large values
        self.assertEqual(format_duration_ns(86400000000000), "24 hours")
        self.assertEqual(format_duration_ms(86400000), "24 hours")

        # Test decimal precision
        self.assertEqual(format_duration_ns(1234), "0 ms")
        self.assertEqual(format_duration_ms(1234), "1 second, 234 ms")

    def test_negative_values(self):
        """Test handling of negative duration values."""
        # Negative values should be handled gracefully
        self.assertEqual(format_duration_ns(-1000), "59 minutes, 59 seconds, 999 ms")
        self.assertEqual(format_duration_ms(-1000), "59 minutes, 59 seconds")

    def test_rounding(self):
        """Test rounding behavior in duration formatting."""
        # Test rounding to one decimal place
        self.assertEqual(format_duration_ns(1234567), "1 ms")
        self.assertEqual(format_duration_ms(1234), "1 second, 234 ms")


if __name__ == "__main__":
    unittest.main()
