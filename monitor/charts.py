"""
Pure visual primitives — no psutil calls here.
Every function takes data and returns a Rich Text (or list of Text).

Braille encoding reference
──────────────────────────
Unicode braille cell layout (8-dot):
  dot1  dot4      bit 0x01  bit 0x08
  dot2  dot5      bit 0x02  bit 0x10
  dot3  dot6      bit 0x04  bit 0x20
  dot7  dot8      bit 0x40  bit 0x80

Base codepoint: U+2800 (⠀).
We fill columns bottom-to-top, giving 4 levels per column and
2× the horizontal density of block-character sparklines.
"""

from __future__ import annotations
from collections import deque
from rich.text import Text
from .config import pct_color

# Bit masks for left/right braille column, 0–4 bars filled from bottom
_L = [0x00, 0x40, 0x44, 0x46, 0x47]
_R = [0x00, 0x80, 0xA0, 0xB0, 0xB8]

# Block characters for fractional fill in the time-series graph
_FRAC = " ▁▂▃▄▅▆▇█"

# Heatmap shades from empty → full
_HEAT = ["  ░░  ", "  ▒▒  ", "  ▓▓  ", "  ██  "]


# ── Sparklines ────────────────────────────────────────────────────────────────

def braille_spark(values: deque, width: int = 30) -> Text:
    """
    High-density sparkline using braille characters.
    Each character encodes TWO data points (left & right columns, 4 levels each).
    """
    data = list(values)[-(width * 2):]
    while len(data) < width * 2:
        data.insert(0, 0.0)
    hi = max(data) or 1.0
    t  = Text()
    for i in range(0, width * 2, 2):
        lv = data[i]
        rv = data[i + 1] if i + 1 < len(data) else 0.0
        l  = min(4, int(lv / hi * 4.9999))
        r  = min(4, int(rv / hi * 4.9999))
        ch = chr(0x2800 | _L[l] | _R[r])
        t.append(ch, style=pct_color((lv + rv) / 2 / hi * 100))
    return t


def block_spark(values: deque, width: int = 30) -> Text:
    """Classic single-value-per-character block sparkline."""
    CHARS = " ▁▂▃▄▅▆▇█"
    data  = list(values)[-width:]
    while len(data) < width:
        data.insert(0, 0.0)
    hi   = max(data) or 1.0
    lo   = min(data)
    span = hi - lo or 1.0
    t    = Text()
    for v in data:
        idx = int((v - lo) / span * (len(CHARS) - 1))
        t.append(CHARS[idx], style=pct_color(v / hi * 100))
    return t


# ── Progress bars ─────────────────────────────────────────────────────────────

def gradient_bar(pct: float, width: int = 28) -> Text:
    """
    Filled bar with a green→yellow→red colour gradient.
    Unfilled portion uses dim ░ characters.
    """
    filled = int(pct / 100 * width)
    t = Text("[", style="dim")
    for i in range(width):
        if i >= filled:
            t.append("░", style="dim")
            continue
        pos = i / width * 100
        if pos < 45:
            style = "bold green"
        elif pos < 72:
            style = "bold yellow"
        else:
            style = "bold red"
        t.append("█", style=style)
    t.append("] ", style="dim")
    t.append(f"{pct:5.1f}%", style=pct_color(pct))
    return t


def mem_bar(used_pct: float, cached_pct: float = 0.0, width: int = 34) -> Text:
    """
    3-segment memory bar: used (red) | cached (yellow) | free (dim green).
    Shows the memory composition at a glance.
    """
    uw = int(used_pct   / 100 * width)
    cw = int(cached_pct / 100 * width)
    fw = max(0, width - uw - cw)
    t  = Text("[", style="dim")
    t.append("█" * uw,  style="bold red")
    t.append("▒" * cw,  style="bold yellow")
    t.append("░" * fw,  style="dim green")
    t.append("] ", style="dim")
    return t


def rel_bar(val: float, max_val: float, width: int = 12) -> Text:
    """Horizontal bar relative to a supplied maximum (for process table)."""
    ratio  = val / max_val if max_val else 0.0
    filled = int(ratio * width)
    t = Text()
    t.append("█" * filled,          style=pct_color(ratio * 100))
    t.append("░" * (width - filled), style="dim")
    return t


# ── 2-D time-series graph ─────────────────────────────────────────────────────

def time_series(
    values:  deque,
    width:   int,
    height:  int,
    max_val: float = 100.0,
) -> Text:
    """
    Render a full 2-D time-series graph using sub-character vertical resolution.
    Y-axis labels appear at top, middle, and bottom.
    Each column represents one sample; value encoded as filled height.
    """
    data = list(values)[-width:]
    while len(data) < width:
        data.insert(0, 0.0)

    scale = max(max(data), max_val, 1.0)
    lines: list[Text] = []

    for row in range(height - 1, -1, -1):
        lo = row       / height * scale
        hi = (row + 1) / height * scale

        if   row == height - 1: label = f"{scale:3.0f}% │"
        elif row == 0:          label = "  0% │"
        elif row == height // 2: label = f"{scale/2:3.0f}% │"
        else:                   label = "     │"

        line = Text(label, style="dim")
        for v in data:
            if v >= hi:
                line.append("█", style=pct_color(v / scale * 100))
            elif v > lo:
                frac = (v - lo) / (hi - lo)
                line.append(_FRAC[min(8, int(frac * 8))],
                             style=pct_color(v / scale * 100))
            else:
                line.append("·", style="dim")
        lines.append(line)

    lines.append(Text(f"     └{'─' * width}", style="dim"))

    out = Text()
    for i, ln in enumerate(lines):
        out.append_text(ln)
        if i < len(lines) - 1:
            out.append("\n")
    return out


# ── CPU core heatmap ──────────────────────────────────────────────────────────

def core_heatmap(cores: list[deque], cols: int = 8) -> Text:
    """
    Renders all CPU cores as a coloured grid.
    Each cell shows the core index, a shade block, and the current percentage.
    Shade intensity: ░░ → ▒▒ → ▓▓ → ██
    """
    t = Text()
    for i, hist in enumerate(cores):
        pct   = list(hist)[-1] if hist else 0.0
        shade = _HEAT[min(len(_HEAT) - 1, int(pct / 100 * len(_HEAT)))]
        style = pct_color(pct)
        t.append(f" C{i:02d}", style="dim")
        t.append("[", style="dim")
        t.append(shade.strip(), style=style)
        t.append("]", style="dim")
        t.append(f"{pct:3.0f}%", style=style)
        if (i + 1) % cols == 0:
            t.append("\n")
        else:
            t.append("  ")
    if len(cores) % cols != 0:
        t.append("\n")
    return t
