"""Tests for source_handler.py"""

import unittest
from os import path
from unittest.mock import patch

import serial

from canmonitor.source_handler import CandumpHandler, InvalidFrame, SerialHandler

TEST_DATA_DIR = path.abspath(path.join(path.dirname(__file__), "data"))


class SerialHandlerTestCase(unittest.TestCase):
    """Test case for source_handler.SerialHandler."""

    def setUp(self):
        self.serial_handler = SerialHandler(
            "LOOP FOR TESTS"
        )  # device_name will not be used
        self.serial_handler.serial_device = serial.serial_for_url("loop://")

    def tearDown(self):
        self.serial_handler.close()

    def test_get_message(self):
        normal_frame = b"FRAME:ID=246:LEN=8:8E:62:1C:F6:1E:63:63:20\n"
        self.serial_handler.serial_device.write(normal_frame)
        frame_id, data = self.serial_handler.get_message()
        self.assertEqual(246, frame_id)
        self.assertEqual(b"\x8e\x62\x1c\xf6\x1e\x63\x63\x20", data)

        no_data_frame = b"FRAME:ID=246:LEN=0:\n"
        self.serial_handler.serial_device.write(no_data_frame)
        frame_id, data = self.serial_handler.get_message()
        self.assertEqual(246, frame_id)
        self.assertEqual(b"", data)

        wrong_length_frame = b"FRAME:ID=246:LEN=9:00:01:02:03:04:05:06:07\n"
        self.serial_handler.serial_device.write(wrong_length_frame)
        self.assertRaises(InvalidFrame, self.serial_handler.get_message)

        three_digit_data_frame = b"FRAME:ID=246:LEN=1:012\n"
        self.serial_handler.serial_device.write(three_digit_data_frame)
        self.assertRaises(InvalidFrame, self.serial_handler.get_message)

        one_digit_data_frame = b"FRAME:ID=246:LEN=1:0\n"
        self.serial_handler.serial_device.write(one_digit_data_frame)
        self.assertRaises(InvalidFrame, self.serial_handler.get_message)

        missing_id_frame = b"FRAME:LEN=1:8E\n"
        self.serial_handler.serial_device.write(missing_id_frame)
        self.assertRaises(InvalidFrame, self.serial_handler.get_message)

        missing_length_frame = b"FRAME:ID=246:8E\n"
        self.serial_handler.serial_device.write(missing_length_frame)
        self.assertRaises(InvalidFrame, self.serial_handler.get_message)


class CandumpHandlerTestCase(unittest.TestCase):
    """Test case for source_handler.CandumpHandler."""

    maxDiff = None

    def setUp(self):
        file_path = path.join(TEST_DATA_DIR, "test_data.log")
        self.candump_handler = CandumpHandler(file_path)
        self.candump_handler.open()

    def tearDown(self):
        self.candump_handler.close()

    @patch("time.sleep")  # Mock time.sleep to avoid delays in tests
    def test_get_message(self, mock_sleep):
        messages = [self.candump_handler.get_message() for _ in range(7)]

        expected_messages = [
            (0x000, b""),
            (0x000, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
            (0xFFF, b"\xff\xff\xff\xff\xff\xff\xff\xff"),
            (0x001, b"\x00\x00\x00\x00\x00\x00\x00\x01"),
            (0x100, b"\x10\x00\x00\x00\x00\x00\x00\x00"),
            (0xABC, b"\x12\xaf\x49"),
            (0x743, b"\x9f\x20\xa1\x20\x78\xbc\xea\x98"),
        ]

        self.assertEqual(expected_messages, messages)

        self.assertRaises(InvalidFrame, self.candump_handler.get_message)
        self.assertRaises(EOFError, self.candump_handler.get_message)
        self.assertRaises(EOFError, self.candump_handler.get_message)

    @patch("time.sleep")
    def test_extended_can_id_ranges(self, mock_sleep):
        """Test extended CAN ID ranges including 32-bit values."""
        # Use the extended test data file
        file_path = path.join(TEST_DATA_DIR, "extended_test_data.log")
        extended_handler = CandumpHandler(file_path)
        extended_handler.open()

        try:
            # Test messages matching extended_test_data.log (25 valid messages)
            test_cases = [
                # First 7 match original test_data.log
                (0x000, b""),
                (0x000, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
                (0xFFF, b"\xff\xff\xff\xff\xff\xff\xff\xff"),
                (0x001, b"\x00\x00\x00\x00\x00\x00\x00\x01"),
                (0x100, b"\x10\x00\x00\x00\x00\x00\x00\x00"),
                (0xABC, b"\x12\xaf\x49"),
                (0x743, b"\x9f\x20\xa1\x20\x78\xbc\xea\x98"),
                # Extended test cases
                (0x001, b"\x0a"),
                (0x7FF, b"\x11\x22\x33\x44\x55\x66\x77\x88"),
                (0x800, b"\xaa\xbb\xcc\xdd\xee\xff\x00\x11"),
                (0x1FFFFFFF, b"\x01\x23\x45\x67\x89\xab\xcd\xef"),
                (0x20000000, b"\xfe\xdc\xba\x98\x76\x54\x32\x10"),
                (0x7FFFFFFF, b"\xff"),
                (0x80000000, b"\x00\x00"),
                (0xFFFFFFFF, b"\xff\xff\xff\xff\xff"),
                (0x12345678, b"\x12\x34\x56"),
                (0xABCDEF01, b"\xab\xcd\xef"),
                (0x246, b"\x8e\x62\x1c\xf6\x1e\x63\x63\x20"),
                (0x100, b"\xff\x00\xff\x00\xff\x00\xff\x00"),
                (0x200, b"\x00\xff\x00\xff\x00\xff\x00\xff"),
                (0x300, b"\x55\x55\xaa\xaa\x55\x55\xaa\xaa"),
                (0x400, b"\xaa\xaa\x55\x55\xaa\xaa\x55\x55"),
                (0x500, b"\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f"),
                (0x600, b"\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0"),
                (0x700, b"\x01\x23\x45\x67\x89\xab\xcd\xef"),
                (0x800, b"\xfe\xdc\xba\x98\x76\x54\x32\x10"),
                (0xB00, b"\x01"),
                (0xC00, b"\x12"),
                (0xD00, b"\x12\x03"),
                (0xE00, b"\x12\x34"),
                (0xF00, b"\x12\x34\x05"),
                (0x1000, b"\x12\x34\x56"),
                (0x1100, b"\x12\x34\x56\x07"),
                (0x1200, b"\x12\x34\x56\x78"),
            ]

            # Read and verify all test messages
            messages = []
            for _ in range(len(test_cases)):
                try:
                    msg = extended_handler.get_message()
                    messages.append(msg)
                except InvalidFrame:
                    # Expected for invalid frames at the end
                    break

            # Verify we got the expected messages
            self.assertEqual(len(messages), len(test_cases))
            for i, (expected_id, expected_data) in enumerate(test_cases):
                with self.subTest(i=i, expected_id=hex(expected_id)):
                    actual_id, actual_data = messages[i]
                    self.assertEqual(
                        actual_id,
                        expected_id,
                        f"ID mismatch at index {i}: expected "
                        f"{hex(expected_id)}, got {hex(actual_id)}",
                    )
                    self.assertEqual(
                        actual_data,
                        expected_data,
                        f"Data mismatch at index {i}: expected "
                        f"{expected_data.hex()}, got {actual_data.hex()}",
                    )

            # Test that invalid frames raise exceptions
            with self.assertRaises(InvalidFrame):
                extended_handler.get_message()  # "invalid frame"

        finally:
            extended_handler.close()
            extended_handler.close()
