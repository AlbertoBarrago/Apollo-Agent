"""Unit tests for the file operations module.

This module contains a comprehensive suite of tests for
 the session management functions in apollo.service.session.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

# tests/test_session.py
import unittest
from unittest.mock import patch, mock_open, call
import json
import datetime
import os

# Module to test
from apollo.service import session as session_service

# Import Constant to be able to patch its attributes where session_service uses them
from apollo.config import const as apollo_const


class TestSessionManagement(unittest.TestCase):

    def setUp(self):
        self.mock_chat_history_dir = "mock_workspace/chat_history"
        self.mock_max_messages = 2
        self.mock_system_new_session_template = "System: New session at {timestamp}"
        # self.mock_system_new_session_prefix = "System: New session at " # Not directly used

        self.mock_today = datetime.date(2023, 10, 26)
        self.mock_strftime_val = "2023-10-26 10:00:00"

        self.expected_filename = (
            f"chat_history_{self.mock_today.strftime('%Y%m%d')}.json"
        )
        self.expected_filepath = os.path.join(
            self.mock_chat_history_dir, self.expected_filename
        )

    def test_get_daily_session_filename(self):
        """Test generation of daily session filename."""
        base_dir = "/test/base"
        with patch("datetime.date") as mock_date_module:  # Renamed to avoid conflict
            mock_date_module.today.return_value = self.mock_today
            expected_path = os.path.join(
                base_dir, f"chat_history_{self.mock_today.strftime('%Y%m%d')}.json"
            )
            self.assertEqual(
                session_service.get_daily_session_filename(base_dir), expected_path
            )

    # Decorator order: bottom-most is applied first, so its arg comes first in method signature
    @patch("builtins.print")
    @patch("time.strftime")
    @patch("json.dump")
    @patch("json.load")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("apollo.service.session.get_daily_session_filename")
    @patch.object(
        apollo_const.Constant,
        "system_new_session",
        new_callable=unittest.mock.PropertyMock,
    )
    @patch.object(apollo_const.Constant, "max_history_messages")
    @patch.object(apollo_const.Constant, "chat_history_dir")
    def run_save_test(
        self,
        # Mocks from decorators (order corresponds to decorator stack, bottom-up)
        mock_const_chat_dir,
        mock_const_max_messages,
        mock_const_system_session_prop,
        mock_get_daily_filename,
        mock_os_makedirs,
        mock_os_exists,
        mock_json_load,
        mock_json_dump,
        mock_time_strftime,
        mock_builtin_print,
        # Test-specific inputs
        message_to_save: str,  # Explicitly named
        role_to_save: str,  # Explicitly named
        # Test-specific mock configurations:
        os_exists_val=False,
        json_load_val=None,
        json_load_effect=None,
        open_read_effect=None,  # For the first open() call if os.path.exists is True
        open_write_effect=None,  # For the second open() call (the write operation)
    ):
        """Helper to run save_user_history_to_json with various mocks."""

        # Configure general mocks based on setUp
        mock_const_system_session_prop.return_value = (
            self.mock_system_new_session_template
        )
        mock_const_max_messages.return_value = self.mock_max_messages
        mock_const_chat_dir.return_value = self.mock_chat_history_dir
        mock_get_daily_filename.return_value = self.expected_filepath
        mock_time_strftime.return_value = self.mock_strftime_val

        # Configure test-specific mocks for os.path.exists and json.load
        mock_os_exists.return_value = os_exists_val
        if json_load_effect:
            mock_json_load.side_effect = json_load_effect
        else:
            mock_json_load.return_value = json_load_val

        # Mock open() behavior for read and write operations
        m_open_mock = mock_open()
        open_effects = []

        if os_exists_val:  # A read attempt will happen first
            if open_read_effect:
                open_effects.append(open_read_effect)
            else:  # Successful read, provide default mock file handle for reading
                open_effects.append(m_open_mock.return_value)

        # All paths will eventually attempt a write operation
        if open_write_effect:
            open_effects.append(open_write_effect)
        else:  # Successful write, provide default mock file handle for writing
            open_effects.append(m_open_mock.return_value)

        m_open_mock.side_effect = open_effects

        with patch("builtins.open", m_open_mock):
            returned_path = session_service.save_user_history_to_json(
                message_to_save, role_to_save
            )

        # The m_open_mock is the mock for the `open` function itself.
        # m_open_mock.return_value is the *default* file handle it would return.
        # If side_effect provided a specific handle for the write call, that's what json.dump got.
        # For simplicity in assertions, we'll use m_open_mock.return_value if the write was meant to succeed
        # and not raise an error during the open("w") call itself.
        # If open_write_effect was an error, json.dump wouldn't be called.
        actual_write_handle = m_open_mock.return_value
        if open_write_effect and not isinstance(open_write_effect, Exception):
            actual_write_handle = open_write_effect

        return (
            returned_path,
            mock_os_makedirs,
            mock_os_exists,
            mock_json_load,
            mock_json_dump,
            mock_time_strftime,
            mock_builtin_print,
            m_open_mock,
            actual_write_handle,
        )

    def test_save_invalid_input(self):
        """Test saving with invalid message or role."""
        # Test invalid message type
        result_tuple = self.run_save_test(message_to_save=123, role_to_save="user")
        returned_path = result_tuple[0]
        mock_print = result_tuple[6]
        mock_print.assert_any_call(
            "[WARNING] Invalid message content or role provided. Skipping save."
        )
        self.assertIsNone(returned_path)

        mock_print.reset_mock()
        # Test empty role
        result_tuple = self.run_save_test(message_to_save="hello", role_to_save="")
        returned_path = result_tuple[0]
        mock_print = result_tuple[6]
        mock_print.assert_any_call(
            "[WARNING] Invalid message content or role provided. Skipping save."
        )
        self.assertIsNone(returned_path)

    def test_save_typeerror_on_json_dump(self):
        """Test TypeError during json.dump (serialization error)."""
        msg, role = "type error", "user"

        with patch("builtins.print") as mock_p, patch(
            "time.strftime", return_value=self.mock_strftime_val
        ), patch(
            "json.dump", side_effect=TypeError("Not serializable")
        ) as mock_jd, patch(
            "json.load", return_value=[]
        ), patch(
            "os.path.exists", return_value=False
        ), patch(
            "os.makedirs"
        ), patch(
            "apollo.service.session.get_daily_session_filename",
            return_value=self.expected_filepath,
        ), patch.object(
            apollo_const.Constant, "chat_history_dir", self.mock_chat_history_dir
        ), patch.object(
            apollo_const.Constant, "max_history_messages", self.mock_max_messages
        ), patch.object(
            apollo_const.Constant,
            "system_new_session",
            self.mock_system_new_session_template,
        ):

            m_open = mock_open()
            with patch("builtins.open", m_open):
                returned_path_direct = session_service.save_user_history_to_json(
                    msg, role
                )

            self.assertEqual(returned_path_direct, self.expected_filepath)
            mock_p.assert_any_call(
                f"[ERROR] JSON serialization error: Not serializable"
            )
            mock_p.assert_any_call(
                "Not saving chat history due to serialization error. Please check message structure."
            )
            mock_jd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
