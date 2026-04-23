"""
Panel builders — one function per dashboard section.
Each returns a Rich renderable suitable for embedding in a Layout.
"""

from __future__ import annotations

import socket
import platform
from datetime import datetime

import psutil
from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .charts import (
    block_spark,
    braille_spark,
    core_heatmap,
    gradient_bar,
    mem_bar,
    rel_bar,
    time_series,
)
from .collector import State
from .config import (
    ACCENT, B_CPU, B_DISK, B_HDR, B_MEM, B_NET, B_PROC, B_TICK,
    CRIT, DIM, GOOD, GRAPH_H, GRAPH_W, HEAT_COLS, PRIMARY, SECONDARY,
    TOP_PROCS, WARN, age_style, load_color, pct_color,
)


# ── Shared formatting helpers ─────────────────────────────────────────────────

def _fb(n: float, suf: str = "B") -> str:
    """Human-readable byte size."""
    for u in ("", "K", "M", "G", "T"):
        if abs(n) < 1024:
            return f"{n:6.1f} {u}{suf}"
        n /= 1024
    return f"{n:.1f} P{suf}"


def _fr(bps: float) -> str:
    return _fb(bps, "B/s")


def _uptime(since: datetime) -> str:
    td = datetime.now() - since
    h, rem = divmod(int(td.total_seconds()), 3600)
    m, s   = divmod(rem, 60)
    if td.days:
        return f"{td.days}d {h % 24:02d}h {m:02d}m"
    return f"{h:02d}h {m:02d}m {s:02d}s"


# ── Header ────────────────────────────────────────────────────────────────────

def make_header(state: State) -> Panel:
    hostname  = socket.gethostname()
    uname     = platform.uname()
    now_time  = datetime.now().strftime("%H:%M:%S")
    now_date  = datetime.now().strftime("%a %d %b %Y")

    try:
        la1, la5, la15 = psutil.getloadavg()
    except AttributeError:
        la1 = la5 = la15 = 0.0

    ncpu = state.n_cpu
    mem  = psutil.virtual_memory()

    top = Text()
    top.append("  ◈ ", style="bold bright_cyan")
    top.append("CLAUDE POWER", style="bold cyan")
    top.append(" SYSMON ", style="bold white")
    top.append("◈", style="bold bright_cyan")
    top.append("  │  ", style="dim")
    top.append(hostname, style="bold white")
    top.append("  │  ", style="dim")
    top.append(f"{uname.system} {uname.release}", style="white")
    top.append("  │  ", style="dim")
    top.append(now_date, style="dim yellow")
    top.append("  ")
    top.append(now_time, style="bold yellow")
    top.append(f"   │  RAM ", style="dim")
    top.append(f"{mem.percent:.0f}%", style=pct_color(mem.percent))
    top.append(f"  Tick #{state.tick}", style="dim")

    bot = Text()
    bot.append("  Sys uptime: ", style="dim")
    bot.append(_uptime(state.boot_time), style=GOOD)
    bot.append("   Session: ", style="dim")
    bot.append(_uptime(state.start_time), style=PRIMARY)
    bot.append("   Load avg: ", style="dim")
    bot.append(f"{la1:.2f}", style=load_color(la1, ncpu))
    bot.append(" · ", style="dim")
    bot.append(f"{la5:.2f}", style=load_color(la5, ncpu))
    bot.append(" · ", style="dim")
    bot.append(f"{la15:.2f}", style=load_color(la15, ncpu))
    bot.append(f"  [1m / 5m / 15m across {ncpu} logical CPUs]", style="dim")

    body = Text()
    body.append_text(top)
    body.append("\n")
    body.append_text(bot)

    return Panel(body, style=B_HDR, padding=(0, 1))


# ── CPU ───────────────────────────────────────────────────────────────────────

def make_cpu(state: State) -> Panel:
    current = list(state.cpu_total)[-1]
    freq    = psutil.cpu_freq()
    fstr    = (f"{freq.current / 1000:.2f} / {freq.max / 1000:.2f} GHz"
               if freq else "N/A")
    phys    = psutil.cpu_count(logical=False)

    body = Text()
    body.append("  Total   ", style="dim")
    body.append_text(gradient_bar(current, 36))
    body.append(f"  {fstr}\n\n", style="dim")

    # Full 2-D time-series graph
    body.append_text(time_series(state.cpu_total, width=GRAPH_W, height=GRAPH_H))
    body.append("\n\n")

    # Core heatmap grid
    body.append("  ── Core Heatmap ", style="dim")
    body.append("─" * 32 + "\n", style="dim")
    body.append_text(core_heatmap(state.cpu_cores, cols=HEAT_COLS))

    title = (f"[{B_CPU}]CPU[/{B_CPU}]  "
             f"[dim]{phys} physical · {state.n_cpu} logical[/dim]")
    return Panel(body, title=title, border_style=B_CPU, padding=(0, 1))


# ── Memory ────────────────────────────────────────────────────────────────────

def make_memory(state: State) -> Panel:
    mem  = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cached_pct = (getattr(mem, "cached", 0) or 0) / (mem.total or 1) * 100

    body = Text()

    body.append("  RAM    ", style="dim")
    body.append_text(mem_bar(mem.percent, cached_pct, 34))
    body.append(f"{_fb(mem.used)} / {_fb(mem.total)}\n", style="white")
    body.append("         ")
    body.append_text(block_spark(state.mem_pct, 48))
    body.append("\n\n")

    body.append("  Swap   ", style="dim")
    body.append_text(gradient_bar(swap.percent, 34))
    body.append(f"  {_fb(swap.used)} / {_fb(swap.total)}\n", style="white")
    body.append("         ")
    body.append_text(block_spark(state.swap_pct, 48))
    body.append("\n\n")

    legend = Text("  ")
    legend.append("█", style="bold red")
    legend.append(" Used   ", style="dim")
    legend.append("▒", style="bold yellow")
    legend.append(" Cached   ", style="dim")
    legend.append("░", style="dim green")
    legend.append(" Free", style="dim")

    return Panel(Group(body, legend),
                 title=f"[{B_MEM}]Memory[/{B_MEM}]",
                 border_style=B_MEM, padding=(0, 1))


# ── Network ───────────────────────────────────────────────────────────────────

def make_network(state: State) -> Panel:
    net  = psutil.net_io_counters()
    up_r = list(state.net_up)[-1]
    dn_r = list(state.net_down)[-1]

    rates = Text()
    rates.append(" ▲ Upload   ", style="bold green")
    rates.append(f"{_fr(up_r):<16}", style="green")
    rates.append_text(braille_spark(state.net_up, 22))
    rates.append(f"  Σ {_fb(net.bytes_sent)}\n", style="dim")
    rates.append(" ▼ Download ", style="bold blue")
    rates.append(f"{_fr(dn_r):<16}", style="blue")
    rates.append_text(braille_spark(state.net_down, 22))
    rates.append(f"  Σ {_fb(net.bytes_recv)}\n", style="dim")

    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim",
                  padding=(0, 1))
    table.add_column("Interface", style="cyan",  min_width=10, no_wrap=True)
    table.add_column("IPv4",      style="white", min_width=15)
    table.add_column("Speed",     justify="right", min_width=9)
    table.add_column("●",         justify="center", min_width=4)

    shown = 0
    for name, addr_list in addrs.items():
        if shown >= 6:
            break
        ip  = next((a.address for a in addr_list
                    if a.family == socket.AF_INET), "—")
        st  = stats.get(name)
        spd = f"{st.speed}Mb/s" if st and st.speed else "—"
        dot = "[bold green]UP[/bold green]" if (st and st.isup) else "[red]DN[/red]"
        table.add_row(name, ip, spd, dot)
        shown += 1

    return Panel(Group(rates, Text(""), table),
                 title=f"[{B_NET}]Network[/{B_NET}]",
                 border_style=B_NET, padding=(0, 1))


# ── Disk ─────────────────────────────────────────────────────────────────────

def make_disk(state: State) -> Panel:
    dr = list(state.disk_r)[-1]
    dw = list(state.disk_w)[-1]

    io = Text()
    io.append(" ▶ Read  ", style="bold yellow")
    io.append(f"{_fr(dr):<16}", style="yellow")
    io.append_text(braille_spark(state.disk_r, 22))
    io.append("\n")
    io.append(" ◀ Write ", style="bold red")
    io.append(f"{_fr(dw):<16}", style="red")
    io.append_text(braille_spark(state.disk_w, 22))
    io.append("\n\n")

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim",
                  padding=(0, 1))
    table.add_column("Mount",  style="cyan",  min_width=12, no_wrap=True)
    table.add_column("FS",     style="white", min_width=5)
    table.add_column("Total",  justify="right")
    table.add_column("Used",   justify="right")
    table.add_column("Free",   style="green", justify="right")
    table.add_column("Usage",  min_width=20)

    for part in psutil.disk_partitions(all=False)[:6]:
        try:
            u = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        table.add_row(
            part.mountpoint[:12],
            part.fstype[:5],
            _fb(u.total),
            _fb(u.used),
            _fb(u.free),
            gradient_bar(u.percent, 12),
        )

    return Panel(Group(io, table),
                 title=f"[{B_DISK}]Disk I/O & Partitions[/{B_DISK}]",
                 border_style=B_DISK, padding=(0, 1))


# ── Processes ─────────────────────────────────────────────────────────────────

def make_processes(state: State) -> Panel:
    procs = []
    for p in psutil.process_iter(
            ["pid", "name", "username", "cpu_percent",
             "memory_percent", "status", "num_threads"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    top      = procs[:TOP_PROCS]
    max_cpu  = max((p.get("cpu_percent") or 0 for p in top), default=0.1)
    max_cpu  = max(max_cpu, 0.1)
    total    = len(procs)
    running  = sum(1 for p in procs if p.get("status") == "running")

    _ST = {
        "running":    "[bold green]RUN[/bold green]",
        "sleeping":   "[dim]SLP[/dim]",
        "idle":       "[dim]IDL[/dim]",
        "disk-sleep": "[yellow]DSK[/yellow]",
        "stopped":    "[red]STP[/red]",
        "zombie":     "[bold red]ZMB[/bold red]",
    }

    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style="bold dim", padding=(0, 1))
    table.add_column("PID",    style="cyan",    justify="right", min_width=7)
    table.add_column("Name",   style="white",   min_width=18, no_wrap=True)
    table.add_column("User",   style="dim",     min_width=10, no_wrap=True)
    table.add_column("CPU%",   justify="right", min_width=6)
    table.add_column("CPU bar",                 min_width=13)
    table.add_column("MEM%",   justify="right", min_width=6)
    table.add_column("Thr",    justify="right", min_width=4)
    table.add_column("St",     justify="center",min_width=4)

    for info in top:
        cpu = info.get("cpu_percent")    or 0.0
        mem = info.get("memory_percent") or 0.0
        thr = info.get("num_threads")    or 0
        st  = _ST.get(info.get("status", ""), info.get("status", "?"))
        table.add_row(
            str(info["pid"]),
            (info.get("name") or "?")[:18],
            (info.get("username") or "?")[:10],
            Text(f"{cpu:5.1f}", style=pct_color(cpu)),
            rel_bar(cpu, max_cpu, 13),
            Text(f"{mem:5.2f}", style=pct_color(mem)),
            str(thr),
            st,
        )

    return Panel(
        table,
        title=f"[{B_PROC}]Top Processes[/{B_PROC}]",
        subtitle=f"[dim]{total} total · {running} running[/dim]",
        border_style=B_PROC,
        padding=(0, 0),
    )


# ── Extras (battery / temps / cpu-info fallback) ──────────────────────────────

def make_extras() -> Panel:
    items: list = []

    # Battery
    try:
        bat = psutil.sensors_battery()
        if bat is not None:
            pct = bat.percent
            bt  = Text()
            bt.append(" Battery  ", style="dim")
            bt.append_text(gradient_bar(pct, 14))
            if bat.power_plugged:
                bt.append("  ⚡ charging", style="bold green")
            else:
                bt.append("  on battery", style="yellow")
            if bat.secsleft not in (
                    psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
                h, rem = divmod(int(bat.secsleft), 3600)
                m, _   = divmod(rem, 60)
                bt.append(f"  {h:02d}h {m:02d}m left", style="dim")
            bt.append("\n")
            items.append(bt)
    except AttributeError:
        pass

    # Temperatures
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            tt = Text()
            count = 0
            for sensor, entries in temps.items():
                for e in entries[:2]:
                    if count >= 4:
                        break
                    label = f"{sensor}/{e.label}" if e.label else sensor
                    clr   = (CRIT if e.current >= 90
                             else WARN if e.current >= 75
                             else GOOD)
                    tt.append(f" {label[:22]:<24}", style="dim")
                    tt.append(f"{e.current:5.1f}°C", style=clr)
                    if e.high:
                        tt.append(f"  hi {e.high:.0f}°C", style="dim")
                    tt.append("\n")
                    count += 1
            if count:
                items.append(tt)
    except AttributeError:
        pass

    # Fallback: CPU static info
    if not items:
        ct = Text()
        freq = psutil.cpu_freq()
        ct.append(" Physical cores:  ", style="dim")
        ct.append(str(psutil.cpu_count(logical=False)), style="white")
        ct.append("\n Logical cores:   ", style="dim")
        ct.append(str(psutil.cpu_count(logical=True)), style="white")
        if freq:
            ct.append(f"\n Min freq: ", style="dim")
            ct.append(f"{freq.min / 1000:.2f} GHz", style="white")
            ct.append(f"\n Max freq: ", style="dim")
            ct.append(f"{freq.max / 1000:.2f} GHz", style="white")
        ct.append("\n")
        items.append(ct)

    return Panel(Group(*items),
                 title="[bold yellow]System[/bold yellow]",
                 border_style="yellow", padding=(0, 1))


# ── Alert ticker ──────────────────────────────────────────────────────────────

def make_ticker(state: State) -> Panel:
    if not state.alerts:
        body = Text()
        body.append("  ● ", style="bold green")
        body.append("All systems nominal", style="green")
        return Panel(body, title="[dim]Events[/dim]",
                     border_style=B_TICK, padding=(0, 0))

    body = Text()
    for alert in reversed(state.alerts[-7:]):
        age   = (datetime.now() - alert.ts).total_seconds()
        fade  = age_style(age)
        ts    = alert.ts.strftime("%H:%M:%S")
        icon  = "▲" if alert.level == "crit" else "●"
        color = f"bold red {fade}".strip()   if alert.level == "crit" \
           else f"bold yellow {fade}".strip()

        body.append(f"  {icon} ", style=color)
        body.append(f"[{ts}] ", style=f"dim {fade}".strip())
        body.append(alert.message + "   ", style=color)

    return Panel(body, title="[dim]Events[/dim]",
                 border_style=B_TICK, padding=(0, 0))
