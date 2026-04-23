"""
Theme constants, colour helpers, and global configuration.
All other modules import from here — no circular deps.
"""

HISTORY   = 120   # seconds of rolling history kept in deques
REFRESH   = 1.0   # live refresh interval (seconds)
GRAPH_W   = 54    # width of CPU time-series graph (columns)
GRAPH_H   = 9     # height of CPU time-series graph (rows)
TOP_PROCS = 11    # max processes shown in the table
HEAT_COLS = 8     # CPU cores per row in the heatmap


# ── Colour functions ──────────────────────────────────────────────────────────

def pct_color(pct: float) -> str:
    """Map a 0-100 percentage to a Rich colour string."""
    if pct >= 90: return "bold red"
    if pct >= 70: return "bold yellow"
    if pct >= 45: return "yellow"
    return "bold green"


def load_color(load: float, ncpu: int) -> str:
    ratio = load / max(ncpu, 1)
    if ratio >= 1.5: return "bold red"
    if ratio >= 1.0: return "bold yellow"
    return "bold green"


def age_style(seconds: float) -> str:
    """Dim old alerts."""
    if seconds > 60:  return "dim"
    if seconds > 30:  return ""
    return "bold"


# ── Palette ───────────────────────────────────────────────────────────────────

PRIMARY   = "bold cyan"
SECONDARY = "bold magenta"
ACCENT    = "bold yellow"
GOOD      = "bold green"
WARN      = "bold yellow"
CRIT      = "bold red"
DIM       = "dim"

B_HDR  = "bright_cyan"
B_CPU  = "cyan"
B_MEM  = "magenta"
B_NET  = "green"
B_DISK = "yellow"
B_PROC = "white"
B_TICK = "dim"
