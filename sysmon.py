"""
Claude Power SysMon — Real-time terminal system monitor.
Demonstrates: async loops, sparkline rendering, live Rich layouts,
process ranking, network delta tracking, and adaptive color coding.
"""

import time
import psutil
import platform
import socket
import os
import sys
import signal
from collections import deque
from datetime import datetime, timedelta
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.bar import Bar
from rich.progress_bar import ProgressBar
from rich import box
from rich.rule import Rule
from rich.align import Align
from rich.style import Style
from rich.padding import Padding

# ─── Config ───────────────────────────────────────────────────────────────────

HISTORY = 60          # sparkline history length
REFRESH  = 1.0        # seconds between redraws
TOP_PROCS = 8         # number of processes to show

# ─── Colour thresholds ────────────────────────────────────────────────────────

def pct_color(pct: float) -> str:
    if pct >= 90: return "bold red"
    if pct >= 70: return "bold yellow"
    if pct >= 50: return "yellow"
    return "bold green"

def temp_color(t: float) -> str:
    if t >= 90: return "bold red"
    if t >= 75: return "bold yellow"
    return "bold green"

# ─── Sparkline ────────────────────────────────────────────────────────────────

SPARK_CHARS = " ▁▂▃▄▅▆▇█"

def sparkline(values: deque, width: int = 30) -> Text:
    """Render a unicode block-character sparkline."""
    data = list(values)[-width:]
    if not data:
        return Text("─" * width, style="dim")
    hi = max(data) or 1
    lo = min(data)
    span = hi - lo or 1
    chars = []
    for v in data:
        idx = int((v - lo) / span * (len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])
    spark = Text("".join(chars))
    # colour each character by its value
    for i, v in enumerate(data):
        spark.stylize(pct_color(v), i, i + 1)
    return spark

# ─── Bytes formatting ─────────────────────────────────────────────────────────

def fmt_bytes(n: float, suffix: str = "B") -> str:
    for unit in ("", "K", "M", "G", "T"):
        if abs(n) < 1024:
            return f"{n:6.1f} {unit}{suffix}"
        n /= 1024
    return f"{n:.1f} P{suffix}"

def fmt_rate(bps: float) -> str:
    return fmt_bytes(bps, "B/s")

# ─── State ────────────────────────────────────────────────────────────────────

class State:
    def __init__(self):
        self.cpu_hist:  list[deque] = [deque([0]*HISTORY, maxlen=HISTORY)
                                       for _ in range(psutil.cpu_count(logical=True) or 1)]
        self.cpu_total: deque = deque([0]*HISTORY, maxlen=HISTORY)
        self.mem_hist:  deque = deque([0]*HISTORY, maxlen=HISTORY)
        self.swap_hist: deque = deque([0]*HISTORY, maxlen=HISTORY)

        # Network
        net = psutil.net_io_counters()
        self.net_sent_prev = net.bytes_sent
        self.net_recv_prev = net.bytes_recv
        self.net_sent_rate: deque = deque([0]*HISTORY, maxlen=HISTORY)
        self.net_recv_rate: deque = deque([0]*HISTORY, maxlen=HISTORY)

        # Disk I/O
        disk = psutil.disk_io_counters()
        self.disk_read_prev  = disk.read_bytes  if disk else 0
        self.disk_write_prev = disk.write_bytes if disk else 0
        self.disk_read_rate:  deque = deque([0]*HISTORY, maxlen=HISTORY)
        self.disk_write_rate: deque = deque([0]*HISTORY, maxlen=HISTORY)

        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.start_time = datetime.now()
        self.tick = 0

    def update(self):
        self.tick += 1

        # CPU
        per = psutil.cpu_percent(percpu=True)
        for i, p in enumerate(per):
            if i < len(self.cpu_hist):
                self.cpu_hist[i].append(p)
        total = psutil.cpu_percent()
        self.cpu_total.append(total)

        # Memory
        mem  = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.mem_hist.append(mem.percent)
        self.swap_hist.append(swap.percent)

        # Network
        net = psutil.net_io_counters()
        self.net_sent_rate.append((net.bytes_sent - self.net_sent_prev) / REFRESH)
        self.net_recv_rate.append((net.bytes_recv - self.net_recv_prev) / REFRESH)
        self.net_sent_prev = net.bytes_sent
        self.net_recv_prev = net.bytes_recv

        # Disk
        disk = psutil.disk_io_counters()
        if disk:
            self.disk_read_rate.append((disk.read_bytes  - self.disk_read_prev)  / REFRESH)
            self.disk_write_rate.append((disk.write_bytes - self.disk_write_prev) / REFRESH)
            self.disk_read_prev  = disk.read_bytes
            self.disk_write_prev = disk.write_bytes

# ─── Render helpers ───────────────────────────────────────────────────────────

def gauge(pct: float, width: int = 20) -> Text:
    filled = int(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    t = Text(f"[{bar}] {pct:5.1f}%")
    t.stylize(pct_color(pct), 1, 1 + filled)
    t.stylize("dim", 1 + filled, 1 + width)
    t.stylize(pct_color(pct), 2 + width)
    return t

def uptime_str(since: datetime) -> str:
    td = datetime.now() - since
    h, rem = divmod(int(td.total_seconds()), 3600)
    m, s   = divmod(rem, 60)
    d      = td.days
    if d:
        return f"{d}d {h%24:02d}h {m:02d}m"
    return f"{h:02d}h {m:02d}m {s:02d}s"

# ─── Panels ───────────────────────────────────────────────────────────────────

def header_panel(state: State) -> Panel:
    hostname = socket.gethostname()
    uname    = platform.uname()
    now      = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    uptime   = uptime_str(state.boot_time)
    session  = uptime_str(state.start_time)

    t = Text()
    t.append("  Claude Power SysMon", style="bold cyan")
    t.append("  |  ", style="dim")
    t.append(hostname, style="bold white")
    t.append("  |  ", style="dim")
    t.append(f"{uname.system} {uname.release}", style="white")
    t.append("  |  ", style="dim")
    t.append(now, style="bold yellow")
    t.append("\n  Sys uptime: ", style="dim")
    t.append(uptime, style="green")
    t.append("   Session: ", style="dim")
    t.append(session, style="cyan")
    t.append(f"   Ticks: {state.tick}", style="dim")

    return Panel(Align.left(t), style="bold blue", padding=(0, 1))


def cpu_panel(state: State) -> Panel:
    cpu_count = psutil.cpu_count(logical=True)
    freq      = psutil.cpu_freq()
    freq_str  = f"{freq.current/1000:.2f} GHz" if freq else "N/A"

    t = Text()
    total = list(state.cpu_total)[-1]
    t.append(f"Total  ", style="dim")
    t.append(gauge(total))
    t.append("  ")
    t.append(sparkline(state.cpu_total, 28))
    t.append(f"  {freq_str}\n", style="dim")

    cols = []
    for i in range(min(cpu_count, len(state.cpu_hist))):
        p = list(state.cpu_hist[i])[-1]
        line = Text()
        line.append(f"  C{i:<2} ", style="dim")
        line.append(gauge(p, 14))
        line.append("  ")
        line.append(sparkline(state.cpu_hist[i], 14))
        cols.append(line)

    for line in cols:
        t.append_text(line)
        t.append("\n")

    return Panel(t, title="[bold cyan]CPU[/bold cyan]",
                 border_style="cyan", padding=(0, 1))


def memory_panel(state: State) -> Panel:
    mem  = psutil.virtual_memory()
    swap = psutil.swap_memory()

    t = Text()
    t.append("RAM   ", style="dim")
    t.append(gauge(mem.percent))
    t.append(f"  {fmt_bytes(mem.used)} / {fmt_bytes(mem.total)}")
    t.append("  ")
    t.append(sparkline(state.mem_hist, 20))
    t.append("\n")

    t.append("Swap  ", style="dim")
    t.append(gauge(swap.percent))
    t.append(f"  {fmt_bytes(swap.used)} / {fmt_bytes(swap.total)}")
    t.append("  ")
    t.append(sparkline(state.swap_hist, 20))
    t.append("\n\n")

    # Memory breakdown bar
    avail_pct  = mem.available / mem.total * 100
    used_pct   = mem.percent
    cached_pct = getattr(mem, 'cached', 0) / mem.total * 100 if mem.total else 0

    t.append("  Free   ", style="bold green")
    t.append(f"{avail_pct:5.1f}%  ", style="green")
    t.append("Used   ", style="bold red")
    t.append(f"{used_pct:5.1f}%  ", style="red")
    if cached_pct:
        t.append("Cached ", style="bold yellow")
        t.append(f"{cached_pct:5.1f}%", style="yellow")

    return Panel(t, title="[bold magenta]Memory[/bold magenta]",
                 border_style="magenta", padding=(0, 1))


def network_panel(state: State) -> Panel:
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    net   = psutil.net_io_counters()

    sent_rate = list(state.net_sent_rate)[-1]
    recv_rate = list(state.net_recv_rate)[-1]

    t = Text()
    t.append("▲ Up   ", style="bold green")
    t.append(f"{fmt_rate(sent_rate):<14}", style="green")
    t.append(sparkline(state.net_sent_rate, 24), )
    t.append(f"  Total: {fmt_bytes(net.bytes_sent)}\n", style="dim")

    t.append("▼ Down ", style="bold blue")
    t.append(f"{fmt_rate(recv_rate):<14}", style="blue")
    t.append(sparkline(state.net_recv_rate, 24))
    t.append(f"  Total: {fmt_bytes(net.bytes_recv)}\n\n", style="dim")

    # Interface table (top 4)
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim",
                  padding=(0, 1))
    table.add_column("Interface", style="cyan",  min_width=12)
    table.add_column("IP",        style="white", min_width=16)
    table.add_column("Speed",     style="green", justify="right")
    table.add_column("Status",    justify="center")

    shown = 0
    for name, addr_list in addrs.items():
        if shown >= 5: break
        ip = next((a.address for a in addr_list
                   if a.family == socket.AF_INET), "—")
        st = stats.get(name)
        speed  = f"{st.speed} Mb/s" if st and st.speed else "—"
        status = "[green]UP[/green]" if (st and st.isup) else "[red]DOWN[/red]"
        table.add_row(name, ip, speed, status)
        shown += 1

    t2 = Text()
    t2.append_text(t)
    return Panel(
        Padding(table, (0, 0)),
        title="[bold green]Network[/bold green]",
        border_style="green", padding=(0, 1),
        subtitle=str(t)
    )


def disk_panel(state: State) -> Panel:
    partitions = psutil.disk_partitions(all=False)
    read_rate  = list(state.disk_read_rate)[-1]
    write_rate = list(state.disk_write_rate)[-1]

    t = Text()
    t.append("R  ", style="bold yellow")
    t.append(f"{fmt_rate(read_rate):<14}", style="yellow")
    t.append(sparkline(state.disk_read_rate, 24))
    t.append("\n")
    t.append("W  ", style="bold red")
    t.append(f"{fmt_rate(write_rate):<14}", style="red")
    t.append(sparkline(state.disk_write_rate, 24))
    t.append("\n\n")

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim",
                  padding=(0, 1))
    table.add_column("Mount",  style="cyan",   min_width=12)
    table.add_column("FS",     style="white",  min_width=6)
    table.add_column("Size",   style="white",  justify="right")
    table.add_column("Used",   style="white",  justify="right")
    table.add_column("Free",   style="white",  justify="right")
    table.add_column("Usage",  min_width=22)

    for part in partitions[:6]:
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        pct = usage.percent
        bar = gauge(pct, 12)
        table.add_row(
            part.mountpoint[:12],
            part.fstype[:6],
            fmt_bytes(usage.total),
            fmt_bytes(usage.used),
            fmt_bytes(usage.free),
            bar,
        )

    return Panel(
        Padding(table, (0, 0)),
        title="[bold yellow]Disk[/bold yellow]",
        border_style="yellow", padding=(0, 1),
        subtitle=str(t),
    )


def process_panel(state: State) -> Panel:
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username',
                                  'cpu_percent', 'memory_percent',
                                  'status', 'num_threads']):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: (x.get('cpu_percent') or 0), reverse=True)

    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style="bold white", padding=(0, 1))
    table.add_column("PID",     style="cyan",   min_width=7,  justify="right")
    table.add_column("Name",    style="white",  min_width=18, no_wrap=True)
    table.add_column("User",    style="dim",    min_width=10, no_wrap=True)
    table.add_column("CPU%",    style="green",  min_width=6,  justify="right")
    table.add_column("MEM%",    style="magenta",min_width=6,  justify="right")
    table.add_column("Threads", style="dim",    min_width=7,  justify="right")
    table.add_column("Status",  min_width=8)

    status_styles = {
        "running":  "[bold green]running[/bold green]",
        "sleeping": "[dim]sleeping[/dim]",
        "disk-sleep":"[yellow]disk-sleep[/yellow]",
        "stopped":  "[red]stopped[/red]",
        "zombie":   "[bold red]zombie[/bold red]",
    }

    for info in procs[:TOP_PROCS]:
        cpu  = info.get('cpu_percent')  or 0.0
        mem  = info.get('memory_percent') or 0.0
        name = (info.get('name') or '?')[:18]
        user = (info.get('username') or '?')[:10]
        st   = info.get('status', '?')
        thr  = info.get('num_threads', 0)

        cpu_style = pct_color(cpu)
        mem_style = pct_color(mem)

        table.add_row(
            str(info['pid']),
            name,
            user,
            Text(f"{cpu:5.1f}", style=cpu_style),
            Text(f"{mem:5.2f}", style=mem_style),
            str(thr),
            status_styles.get(st, st),
        )

    total_procs  = len(procs)
    running = sum(1 for p in procs if p.get('status') == 'running')

    return Panel(
        table,
        title=f"[bold white]Top Processes[/bold white]  [dim]({total_procs} total, {running} running)[/dim]",
        border_style="white", padding=(0, 0),
    )


def temps_panel() -> Panel | None:
    try:
        temps = psutil.sensors_temperatures()
    except AttributeError:
        return None
    if not temps:
        return None

    t = Text()
    for name, entries in list(temps.items())[:3]:
        for e in entries[:2]:
            label = f"{name}/{e.label}" if e.label else name
            cur   = e.current
            hi    = e.high or 100
            t.append(f"{label[:20]:<22}", style="dim")
            t.append(f"{cur:5.1f}°C", style=temp_color(cur))
            if e.high:
                t.append(f"  (hi {e.high:.0f}°C)", style="dim")
            t.append("\n")

    return Panel(t, title="[bold red]Temperatures[/bold red]",
                 border_style="red", padding=(0, 1))


def battery_panel() -> Panel | None:
    try:
        bat = psutil.sensors_battery()
    except AttributeError:
        return None
    if bat is None:
        return None

    pct = bat.percent
    plugged = bat.power_plugged
    secs_left = bat.secsleft

    t = Text()
    t.append("Battery: ", style="dim")
    t.append(gauge(pct, 20))
    t.append("  ")
    if plugged:
        t.append("CHARGING", style="bold green")
    else:
        t.append("ON BATTERY", style="bold yellow")
    if secs_left not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
        td = timedelta(seconds=int(secs_left))
        t.append(f"  {td} remaining", style="dim")

    return Panel(t, title="[bold yellow]Battery[/bold yellow]",
                 border_style="yellow", padding=(0, 1))


# ─── Layout builder ───────────────────────────────────────────────────────────

def build_layout(state: State) -> Layout:
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["body"].split_row(
        Layout(name="left",  ratio=2),
        Layout(name="right", ratio=3),
    )

    layout["left"].split_column(
        Layout(name="cpu",    ratio=3),
        Layout(name="mem",    ratio=2),
    )

    layout["right"].split_column(
        Layout(name="top_right", ratio=3),
        Layout(name="bot_right", ratio=2),
    )

    layout["top_right"].split_row(
        Layout(name="network", ratio=1),
        Layout(name="disk",    ratio=1),
    )

    layout["bot_right"].split_row(
        Layout(name="procs", ratio=3),
        Layout(name="extras", ratio=1),
    )

    # Assign content
    layout["header"].update(header_panel(state))
    layout["cpu"].update(cpu_panel(state))
    layout["mem"].update(memory_panel(state))
    layout["network"].update(network_panel(state))
    layout["disk"].update(disk_panel(state))
    layout["procs"].update(process_panel(state))

    extras = []
    tp = temps_panel()
    if tp: extras.append(tp)
    bp = battery_panel()
    if bp: extras.append(bp)

    if extras:
        layout["extras"].update(extras[0] if len(extras) == 1
                                else Panel(Text("\n").join(
                                    [Text(str(e)) for e in extras])))
    else:
        info = psutil.cpu_count(logical=False)
        t = Text()
        t.append(f"Physical cores:  {psutil.cpu_count(logical=False)}\n", style="white")
        t.append(f"Logical cores:   {psutil.cpu_count(logical=True)}\n",  style="white")
        freq = psutil.cpu_freq()
        if freq:
            t.append(f"Min freq: {freq.min/1000:.2f} GHz\n", style="dim")
            t.append(f"Max freq: {freq.max/1000:.2f} GHz\n", style="dim")
        layout["extras"].update(
            Panel(t, title="[bold cyan]CPU Info[/bold cyan]",
                  border_style="cyan", padding=(0, 1)))

    legend = Text()
    legend.append("  [green]●[/green] Good  ", style="green")
    legend.append("[yellow]●[/yellow] Moderate  ", style="yellow")
    legend.append("[red]●[/red] High  ", style="red")
    legend.append("  Refreshes every 1s  ", style="dim")
    legend.append("  Press ", style="dim")
    legend.append("Ctrl+C", style="bold white")
    legend.append(" to exit", style="dim")
    layout["footer"].update(
        Panel(Align.center(legend), style="dim", border_style="dim"))

    return layout


# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    console = Console()
    state   = State()

    # Warm up cpu_percent (first call always returns 0)
    psutil.cpu_percent(percpu=True)
    time.sleep(0.1)

    console.print(Panel(
        Align.center(
            Text("Claude Power SysMon  —  initialising…", style="bold cyan")
        ),
        border_style="cyan",
    ))
    time.sleep(0.5)

    try:
        with Live(build_layout(state), console=console,
                  refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(REFRESH)
                state.update()
                live.update(build_layout(state))

    except KeyboardInterrupt:
        console.print("\n[bold cyan]SysMon exited. Goodbye![/bold cyan]")


if __name__ == "__main__":
    main()
