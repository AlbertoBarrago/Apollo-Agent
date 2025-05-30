"""Unit tests for the JSON encoder module.

This module contains comprehensive unit tests for the JSON encoder functionality,
focusing on custom encoding of various Python objects.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from datetime import datetime, date, time
from decimal import Decimal
from apollo.encoder.json_encoder import ApolloJSONEncoder


class TestApolloJSONEncoder(unittest.TestCase):
    """Test cases for the ApolloJSONEncoder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.encoder = ApolloJSONEncoder()

    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        result = self.encoder.default(test_datetime)
        self.assertEqual(result, str(test_datetime))

    def test_encode_date(self):
        """Test encoding date objects."""
        test_date = date(2023, 1, 1)
        result = self.encoder.default(test_date)
        self.assertEqual(result, test_date.isoformat())

    def test_encode_time(self):
        """Test encoding time objects."""
        test_time = time(12, 0, 0)
        result = self.encoder.default(test_time)
        self.assertEqual(result, test_time.isoformat())

    def test_encode_complex_object(self):
        """Test encoding complex objects with multiple nested types."""
        complex_obj = {
            "datetime": datetime(2023, 1, 1, 12, 0, 0),
            "date": date(2023, 1, 1),
            "time": time(12, 0, 0),
            "decimal": Decimal("10.5"),
            "bytes": b"test",
            "set": {1, 2, 3},
        }

        # This should not raise any exceptions
        encoded = self.encoder.encode(complex_obj)
        self.assertIsInstance(encoded, str)

    def test_encode_none(self):
        """Test encoding None value."""
        result = self.encoder.encode(None)
        self.assertEqual(result, "null")

    def test_encode_empty_containers(self):
        """Test encoding empty containers."""
        self.assertEqual(self.encoder.encode([]), "[]")
        self.assertEqual(self.encoder.encode({}), "{}")


if __name__ == "__main__":
    unittest.main()
