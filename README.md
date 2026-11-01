# mini_color_convert

Convert between hex, RGB and HSL without rounding drift.

```python
from mini_color_convert import (
    RGB,
    HSL,
    parse_hex,
    parse_rgb,
    parse_hsl,
    format_hex,
    format_rgb,
    format_hsl,
    rgb_to_hsl,
    hsl_to_rgb,
    hex_to_rgb,
    rgb_to_hex,
    hsl_to_hex,
    hex_to_hsl,
)

parse_hex("#ff8000")            # RGB(r=255, g=128, b=0)
parse_rgb("rgb(255, 128, 0)")   # RGB(r=255, g=128, b=0)
parse_hsl("hsl(120, 50%, 25%)") # HSL(h=120.0, s=0.5, l=0.25)

format_hex(RGB(255, 128, 0))    # '#ff8000'
format_rgb(RGB(255, 128, 0))    # 'rgb(255, 128, 0)'
format_hsl(HSL(120.0, 0.5, 0.25))  # 'hsl(120, 50%, 25%)'

rgb_to_hsl(RGB(255, 0, 0))      # HSL(h=0.0, s=1.0, l=0.5)
hsl_to_rgb(HSL(0.0, 1.0, 0.5))  # RGB(r=255, g=0, b=0)
hex_to_hsl("#ffffff")            # HSL(h=0.0, s=0.0, l=1.0)
hsl_to_hex(HSL(240.0, 1.0, 0.5))  # '#0000ff'
```

## Why this exists

Most colour conversion snippets round each intermediate channel before doing
the next conversion, so `hex -> rgb -> hsl -> rgb -> hex` drifts by a unit or
two.  This library keeps the canonical representation for each format and
rounds exactly once, at the boundary where a human-readable string is
produced.  The trade-off is that `RGB` is stored as integers and `HSL` as
floats in fixed ranges; there is no 0..1 RGB variant and no alpha channel.
If you need those, this is not the right library.

## The edge you will hit

`parse_hsl` accepts a hue outside `[0, 360)` and normalises it, so
`hsl(-90, 100%, 50%)` becomes hue `270`.  `format_hsl` prints the hue with
at most two decimals and the S/L channels as integer percentages, which
means `format_hsl` only round-trips through `parse_hsl` to two decimal
places of hue and one percent of S/L.  If you need exact float round-trips,
use the `HSL` object directly rather than its string form.

## API

- `RGB(r, g, b)` — integer channels in `0..255`.
- `HSL(h, s, l)` — hue degrees `[0, 360)`, saturation and lightness in `[0, 1]`.
- `parse_hex(text)` / `parse_rgb(text)` / `parse_hsl(text)` — strict parsers,
  raising `ValueError` on malformed input.
- `format_hex(color)` / `format_rgb(color)` / `format_hsl(color)` — formatters
  that clamp out-of-range channels before printing.
- `rgb_to_hsl(color)` / `hsl_to_rgb(color)` — direct conversions.
- `hex_to_rgb(text)` / `rgb_to_hex(color)` / `hsl_to_hex(color)` /
  `hex_to_hsl(text)` — convenience wrappers around the parser/formatter pair.
