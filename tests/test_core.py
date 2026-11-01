"""Tests for mini_color_convert.core.

These tests pin down the exact behaviour the library claims to support:
strict parsing, clamping on formatting, and single-rounding conversion.
"""

import unittest

from mini_color_convert import (
    HSL,
    RGB,
    format_hex,
    format_hsl,
    format_rgb,
    hex_to_hsl,
    hex_to_rgb,
    hsl_to_hex,
    hsl_to_rgb,
    parse_hex,
    parse_hsl,
    parse_rgb,
    rgb_to_hex,
    rgb_to_hsl,
)


class TestParseHex(unittest.TestCase):
    def test_six_digit_with_hash(self):
        self.assertEqual(parse_hex("#ff8000"), RGB(255, 128, 0))

    def test_six_digit_without_hash(self):
        self.assertEqual(parse_hex("ff8000"), RGB(255, 128, 0))

    def test_three_digit_expands(self):
        self.assertEqual(parse_hex("#f80"), RGB(255, 136, 0))

    def test_uppercase_accepted(self):
        self.assertEqual(parse_hex("#FF8000"), RGB(255, 128, 0))

    def test_whitespace_stripped(self):
        self.assertEqual(parse_hex("  #000000  "), RGB(0, 0, 0))

    def test_rejects_bad_length(self):
        with self.assertRaises(ValueError):
            parse_hex("#ff80")

    def test_rejects_non_hex_digits(self):
        with self.assertRaises(ValueError):
            parse_hex("#gggggg")

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            parse_hex(0xFF8000)


class TestParseRGB(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_rgb("rgb(255, 128, 0)"), RGB(255, 128, 0))

    def test_no_spaces(self):
        self.assertEqual(parse_rgb("rgb(0,0,0)"), RGB(0, 0, 0))

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_rgb("rgb(256, 0, 0)")

    def test_rejects_missing_channel(self):
        with self.assertRaises(ValueError):
            parse_rgb("rgb(1, 2)")


class TestParseHSL(unittest.TestCase):
    def test_basic(self):
        parsed = parse_hsl("hsl(120, 50%, 25%)")
        self.assertAlmostEqual(parsed.h, 120.0)
        self.assertAlmostEqual(parsed.s, 0.5)
        self.assertAlmostEqual(parsed.l, 0.25)

    def test_negative_hue_normalised(self):
        parsed = parse_hsl("hsl(-90, 100%, 50%)")
        self.assertAlmostEqual(parsed.h, 270.0)

    def test_hue_over_360_normalised(self):
        parsed = parse_hsl("hsl(450, 100%, 50%)")
        self.assertAlmostEqual(parsed.h, 90.0)

    def test_rejects_bad_percentage(self):
        with self.assertRaises(ValueError):
            parse_hsl("hsl(120, 150%, 50%)")


class TestFormatting(unittest.TestCase):
    def test_format_hex_lowercase(self):
        self.assertEqual(format_hex(RGB(255, 128, 0)), "#ff8000")

    def test_format_hex_clamps(self):
        self.assertEqual(format_hex(RGB(300, -5, 128)), "#ff0080")

    def test_format_rgb(self):
        self.assertEqual(format_rgb(RGB(1, 2, 3)), "rgb(1, 2, 3)")

    def test_format_hsl_round_trip_through_parse(self):
        text = format_hsl(HSL(120.0, 0.5, 0.25))
        parsed = parse_hsl(text)
        self.assertAlmostEqual(parsed.h, 120.0, places=2)
        self.assertAlmostEqual(parsed.s, 0.5, places=2)
        self.assertAlmostEqual(parsed.l, 0.25, places=2)

    def test_format_hsl_zero_hue_has_no_signed_zero(self):
        self.assertEqual(format_hsl(HSL(-0.0, 0.0, 0.0)), "hsl(0, 0%, 0%)")


class TestConversions(unittest.TestCase):
    def test_rgb_to_hsl_red(self):
        hsl = rgb_to_hsl(RGB(255, 0, 0))
        self.assertAlmostEqual(hsl.h, 0.0)
        self.assertAlmostEqual(hsl.s, 1.0)
        self.assertAlmostEqual(hsl.l, 0.5)

    def test_rgb_to_hsl_grey_has_zero_saturation(self):
        hsl = rgb_to_hsl(RGB(128, 128, 128))
        self.assertAlmostEqual(hsl.h, 0.0)
        self.assertAlmostEqual(hsl.s, 0.0)

    def test_hsl_to_rgb_red(self):
        self.assertEqual(hsl_to_rgb(HSL(0.0, 1.0, 0.5)), RGB(255, 0, 0))

    def test_hsl_to_rgb_grey(self):
        self.assertEqual(hsl_to_rgb(HSL(0.0, 0.0, 0.5)), RGB(128, 128, 128))

    def test_rgb_hsl_round_trip_is_stable(self):
        for original in (RGB(0, 0, 0), RGB(255, 255, 255), RGB(12, 34, 56),
                         RGB(200, 100, 50), RGB(1, 2, 3)):
            back = hsl_to_rgb(rgb_to_hsl(original))
            self.assertEqual(back, original, f"round trip failed for {original}")

    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#010203"), RGB(1, 2, 3))

    def test_rgb_to_hex(self):
        self.assertEqual(rgb_to_hex(RGB(1, 2, 3)), "#010203")

    def test_hex_to_hsl_white(self):
        hsl = hex_to_hsl("#ffffff")
        self.assertAlmostEqual(hsl.h, 0.0)
        self.assertAlmostEqual(hsl.s, 0.0)
        self.assertAlmostEqual(hsl.l, 1.0)

    def test_hsl_to_hex_blue(self):
        self.assertEqual(hsl_to_hex(HSL(240.0, 1.0, 0.5)), "#0000ff")


if __name__ == "__main__":
    unittest.main()
