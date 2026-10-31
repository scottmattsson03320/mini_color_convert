"""Core conversion routines for mini_color_convert.

Design notes
------------
* ``RGB`` stores channels as integers in ``0..255``.  ``HSL`` stores hue in
  degrees ``[0, 360)`` and saturation/lightness as floats in ``[0, 1]``.
  Keeping the two representations distinct avoids the classic bug where a
  caller passes a 0..1 float where a 0..255 int is expected.
* Round-tripping is the whole point of the library, so ``hsl_to_rgb`` uses
  the standard piecewise formula and then rounds with ``round`` (banker's
  rounding is fine here because we clamp first).  We never accumulate float
  error across conversions: every public function takes the canonical input
  representation and produces the canonical output representation.
* Parsing is deliberately strict.  ``parse_hex`` accepts ``#rgb``, ``#rrggbb``
  and the same without the leading ``#``.  ``parse_rgb`` accepts ``rgb(r,g,b)``
  with integer channels.  ``parse_hsl`` accepts ``hsl(h,s%,l%)`` with a
  float hue and percentage saturation/lightness.  Anything else raises
  ``ValueError`` with a message that names the offending input.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class RGB(NamedTuple):
    """An 8-bit RGB colour.  Channels are integers in ``0..255``."""

    r: int
    g: int
    b: int


class HSL(NamedTuple):
    """An HSL colour.  Hue in degrees ``[0, 360)``, S and L in ``[0, 1]``."""

    h: float
    s: float
    l: float


_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_RE = re.compile(
    r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$"
)
_HSL_RE = re.compile(
    r"^hsl\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)%\s*,"
    r"\s*(-?\d+(?:\.\d+)?)%\s*\)$"
)


def _clamp_channel(value: int) -> int:
    """Clamp an integer to the 0..255 range."""
    if value < 0:
        return 0
    if value > 255:
        return 255
    return value


def _clamp_unit(value: float) -> float:
    """Clamp a float to the closed unit interval."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _normalise_hue(value: float) -> float:
    """Wrap a hue in degrees into ``[0, 360)``.

    Negative hues and hues >= 360 are folded back; ``-0.0`` is normalised
    to ``0.0`` so equality checks in tests are not surprised by signed zero.
    """
    value = value % 360.0
    if value == 0.0:
        return 0.0
    return value


def parse_hex(text: str) -> RGB:
    """Parse ``#rgb`` or ``#rrggbb`` (the ``#`` is optional).

    Raises ``ValueError`` on malformed input or out-of-range channels.
    """
    if not isinstance(text, str):
        raise ValueError(f"hex colour must be a string, got {type(text).__name__}")
    match = _HEX_RE.match(text.strip())
    if match is None:
        raise ValueError(f"invalid hex colour: {text!r}")
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return RGB(r, g, b)


def parse_rgb(text: str) -> RGB:
    """Parse ``rgb(r, g, b)`` with integer channels in ``0..255``.

    Raises ``ValueError`` on malformed input or out-of-range channels.
    """
    if not isinstance(text, str):
        raise ValueError(f"rgb colour must be a string, got {type(text).__name__}")
    match = _RGB_RE.match(text.strip())
    if match is None:
        raise ValueError(f"invalid rgb colour: {text!r}")
    r, g, b = (int(part) for part in match.groups())
    for name, value in (("r", r), ("g", g), ("b", b)):
        if not 0 <= value <= 255:
            raise ValueError(f"rgb channel {name}={value} out of range 0..255")
    return RGB(r, g, b)


def parse_hsl(text: str) -> HSL:
    """Parse ``hsl(h, s%, l%)`` with a float hue and percentage S/L.

    Raises ``ValueError`` on malformed input, out-of-range percentages, or
    a hue that is not finite.
    """
    if not isinstance(text, str):
        raise ValueError(f"hsl colour must be a string, got {type(text).__name__}")
    match = _HSL_RE.match(text.strip())
    if match is None:
        raise ValueError(f"invalid hsl colour: {text!r}")
    hue = float(match.group(1))
    sat = float(match.group(2)) / 100.0
    light = float(match.group(3)) / 100.0
    if not -1e9 < hue < 1e9:
        raise ValueError(f"hsl hue {hue!r} is not finite")
    if not 0.0 <= sat <= 1.0:
        raise ValueError(f"hsl saturation {sat!r} out of range 0..1")
    if not 0.0 <= light <= 1.0:
        raise ValueError(f"hsl lightness {light!r} out of range 0..1")
    return HSL(_normalise_hue(hue), sat, light)


def format_hex(color: RGB) -> str:
    """Format an ``RGB`` as ``#rrggbb`` in lowercase."""
    r = _clamp_channel(int(color.r))
    g = _clamp_channel(int(color.g))
    b = _clamp_channel(int(color.b))
    return f"#{r:02x}{g:02x}{b:02x}"


def format_rgb(color: RGB) -> str:
    """Format an ``RGB`` as ``rgb(r, g, b)``."""
    r = _clamp_channel(int(color.r))
    g = _clamp_channel(int(color.g))
    b = _clamp_channel(int(color.b))
    return f"rgb({r}, {g}, {b})"


def format_hsl(color: HSL) -> str:
    """Format an ``HSL`` as ``hsl(h, s%, l%)``.

    Hue is printed with at most two decimals; S and L are printed as integer
    percentages.  This matches what ``parse_hsl`` accepts, so format/parse
    round-trips are stable.
    """
    hue = _normalise_hue(float(color.h))
    sat = _clamp_unit(float(color.s))
    light = _clamp_unit(float(color.l))
    hue_text = f"{hue:.2f}".rstrip("0").rstrip(".")
    if hue_text == "-0":
        hue_text = "0"
    return f"hsl({hue_text}, {round(sat * 100)}%, {round(light * 100)}%)"


def rgb_to_hsl(color: RGB) -> HSL:
    """Convert an ``RGB`` colour to ``HSL``.

    Channels are first clamped to ``0..255`` so that a caller passing an
    out-of-range integer still gets a well-defined result.
    """
    r = _clamp_channel(int(color.r)) / 255.0
    g = _clamp_channel(int(color.g)) / 255.0
    b = _clamp_channel(int(color.b)) / 255.0

    mx = max(r, g, b)
    mn = min(r, g, b)
    lightness = (mx + mn) / 2.0
    if mx == mn:
        return HSL(0.0, 0.0, lightness)

    delta = mx - mn
    if lightness > 0.5:
        saturation = delta / (2.0 - mx - mn)
    else:
        saturation = delta / (mx + mn)

    if mx == r:
        hue = (g - b) / delta
    elif mx == g:
        hue = 2.0 + (b - r) / delta
    else:
        hue = 4.0 + (r - g) / delta
    hue *= 60.0
    return HSL(_normalise_hue(hue), saturation, lightness)


def hsl_to_rgb(color: HSL) -> RGB:
    """Convert an ``HSL`` colour to ``RGB``.

    Uses the standard piecewise formula and rounds to the nearest integer.
    Rounding happens once, at the end, so repeated conversions do not drift.
    """
    hue = _normalise_hue(float(color.h))
    sat = _clamp_unit(float(color.s))
    light = _clamp_unit(float(color.l))

    if sat == 0.0:
        channel = light
        return RGB(round(channel * 255), round(channel * 255), round(channel * 255))

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0.0:
            t += 1.0
        if t > 1.0:
            t -= 1.0
        if t < 1.0 / 6.0:
            return p + (q - p) * 6.0 * t
        if t < 1.0 / 2.0:
            return q
        if t < 2.0 / 3.0:
            return p + (q - p) * (2.0 / 3.0 - t) * 6.0
        return p

    if light < 0.5:
        q = light * (1.0 + sat)
    else:
        q = light + sat - light * sat
    p = 2.0 * light - q
    h = hue / 360.0
    r = hue_to_rgb(p, q, h + 1.0 / 3.0)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1.0 / 3.0)
    return RGB(round(r * 255), round(g * 255), round(b * 255))


def hex_to_rgb(text: str) -> RGB:
    """Parse a hex string and return its ``RGB`` representation."""
    return parse_hex(text)


def rgb_to_hex(color: RGB) -> str:
    """Format an ``RGB`` colour as ``#rrggbb``."""
    return format_hex(color)


def hsl_to_hex(color: HSL) -> str:
    """Convert an ``HSL`` colour to ``#rrggbb``."""
    return format_hex(hsl_to_rgb(color))


def hex_to_hsl(text: str) -> HSL:
    """Parse a hex string and return its ``HSL`` representation."""
    return rgb_to_hsl(parse_hex(text))
