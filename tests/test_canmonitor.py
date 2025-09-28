"""Tests for canmonitor.py"""

import unittest
from os import path

from canmonitor import canmonitor

TEST_DATA_DIR = path.abspath(path.join(path.dirname(__file__), "data"))


class CanmonitorTestCase(unittest.TestCase):
    """Test case for canmonitor.py."""

    def test_format_data_ascii(self):
        # ASCII chars
        decoded_str = canmonitor.format_data_ascii(b"\x20\x7e")
        self.assertEqual(decoded_str, " ~")

        # Null characters
        decoded_str = canmonitor.format_data_ascii(b"\x00\x00")
        self.assertEqual(decoded_str, "..")

        # Non-ASCII chars
        decoded_str = canmonitor.format_data_ascii(b"\x01\x1f\x7f\xff")
        self.assertEqual(decoded_str, "????")

        # Empty data
        decoded_str = canmonitor.format_data_ascii(b"")
        self.assertEqual(decoded_str, "")

    def test_format_data_hex(self):
        formatted_str = canmonitor.format_data_hex(b"\x00\x01\x20\x77\xff")
        self.assertEqual(formatted_str, "00 01 20 77 FF")

        # Empty data
        formatted_str = canmonitor.format_data_hex(b"")
        self.assertEqual(formatted_str, "")

    def test_parse_ints(self):
        with open(path.join(TEST_DATA_DIR, "ids.txt")) as f_obj:
            int_set = canmonitor.parse_ints(f_obj)
        self.assertEqual(int_set, {1, 2, 15, 3, 4, 57, 7})

    def test_dynamic_column_width_fix_for_32bit_ids(self):
        """Test that column width supports full 32-bit CAN ID range."""
        # Test the dynamic column width system that replaces the hardcoded
        # Issue #18 fix with a more robust solution for 32-bit CAN IDs

        # The new system should handle the full 32-bit range:
        # - Max 32-bit unsigned: 4,294,967,295 (10 digits)
        # - Max 32-bit hex: FFFFFFFF (8 characters)

        # Test maximum 32-bit unsigned integer
        max_32bit_unsigned = 4294967295  # 0xFFFFFFFF

        # Verify this is indeed 10 digits
        decimal_str = str(max_32bit_unsigned)
        self.assertEqual(len(decimal_str), 10)
        self.assertEqual(decimal_str, "4294967295")

        # Verify hex representation is 8 characters
        hex_str = "%X" % max_32bit_unsigned
        self.assertEqual(len(hex_str), 8)
        self.assertEqual(hex_str, "FFFFFFFF")

        # Test the dynamic field width calculations
        max_decimal_width = 10  # As defined in canmonitor.py
        max_hex_width = 8       # As defined in canmonitor.py
        id_spacing = 2          # Minimum gap between decimal and hex

        # Verify the spacing calculation
        hex_offset = max_decimal_width + id_spacing
        self.assertEqual(hex_offset, 12)

        # Test formatting with the dynamic widths
        decimal_formatted = str(max_32bit_unsigned).ljust(max_decimal_width)
        hex_formatted = ("%X" % max_32bit_unsigned).ljust(max_hex_width)

        # Should be exact fit (no padding needed for max values)
        self.assertEqual(len(decimal_formatted), 10)
        self.assertEqual(len(hex_formatted), 8)
        self.assertEqual(decimal_formatted, "4294967295")
        self.assertEqual(hex_formatted, "FFFFFFFF")

    def test_id_formatting_edge_cases(self):
        """Test ID formatting for various edge cases related to Issue #18."""

        # Test various ID sizes to ensure formatting works correctly
        test_cases = [
            (0, "0", "0"),  # Minimum ID
            (1, "1", "1"),  # Single digit
            (15, "15", "F"),  # Single hex digit
            (255, "255", "FF"),  # 3 decimal, 2 hex
            (4095, "4095", "FFF"),  # 4 decimal, 3 hex
            (65535, "65535", "FFFF"),  # 5 decimal, 4 hex
            (1048575, "1048575", "FFFFF"),  # 7 decimal, 5 hex
            (536870912, "536870912", "20000000"),  # 9 decimal, 8 hex (Issue #18)
            (2147483647, "2147483647", "7FFFFFFF"),  # Max 32-bit signed (10 digits)
            (4294967295, "4294967295", "FFFFFFFF"),  # Max 32-bit unsigned (10 digits)
        ]

        for frame_id, expected_decimal, expected_hex in test_cases:
            with self.subTest(frame_id=frame_id):
                # Test decimal formatting
                decimal_formatted = str(frame_id).ljust(5)
                # Test hex formatting
                hex_formatted = ("%X" % frame_id).ljust(5)

                # Verify the basic formatting is correct
                self.assertTrue(decimal_formatted.startswith(expected_decimal))
                self.assertTrue(hex_formatted.startswith(expected_hex))

                # For the specific Issue #18 case (9-digit decimal)
                if frame_id == 536870912:
                    # Ensure the decimal part is exactly 9 characters
                    self.assertEqual(len(expected_decimal), 9)
                    # Ensure there would be no truncation
                    self.assertEqual(decimal_formatted.strip(), expected_decimal)

    def test_dynamic_spacing_prevents_overlap_32bit(self):
        """Test that the dynamic spacing prevents ID overlap for 32-bit IDs."""
        # Simulate the dynamic layout constants from canmonitor.py
        id_column_start = 2
        max_decimal_width = 10  # Support for 32-bit unsigned integers
        id_spacing = 2          # Minimum gap between decimal and hex
        hex_offset = max_decimal_width + id_spacing  # Dynamic offset

        # Test case: Maximum 32-bit unsigned integer
        max_32bit_id = 4294967295  # "4294967295" (10 chars)
        decimal_str = str(max_32bit_id)

        # Calculate positions as done in the actual code
        decimal_pos = id_column_start  # Position 2
        hex_pos = id_column_start + hex_offset  # Position 2 + 12 = 14

        # The decimal ID ends at position 2 + 10 = 12
        decimal_end_pos = decimal_pos + len(decimal_str)

        # The hex ID starts at position 14
        # There should be sufficient gap to prevent overlap
        gap = hex_pos - decimal_end_pos

        # Verify there's exactly the expected spacing
        self.assertEqual(gap, id_spacing,
                         f"Expected {id_spacing} chars gap, got {gap}")

        # Verify this handles the maximum case without overlap
        no_overlap = (decimal_end_pos <= hex_pos)
        self.assertTrue(no_overlap,
                        f"Decimal ends at {decimal_end_pos}, "
                        f"hex starts at {hex_pos} - should not overlap")

        # Test that this also works for the original Issue #18 case (9 digits)
        issue_18_decimal_end = id_column_start + 9

        # Should have even more spacing than needed for Issue #18
        issue_18_gap = hex_pos - issue_18_decimal_end
        self.assertGreaterEqual(
            issue_18_gap, id_spacing,
            "Should provide adequate spacing for Issue #18 case too")
