"""
System data collector.
Maintains rolling deques for every metric and generates timed alerts.
"""

import psutil
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from .config import HISTORY, REFRESH


@dataclass
class Alert:
    ts:      datetime
    level:   str      # "info" | "warn" | "crit"
    message: str


class State:
    """Accumulates all sampled metrics; call .update() once per tick."""

    def __init__(self) -> None:
        self.n_cpu = psutil.cpu_count(logical=True) or 1

        # CPU
        self.cpu_total = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.cpu_cores = [
            deque([0.0] * HISTORY, maxlen=HISTORY)
            for _ in range(self.n_cpu)
        ]

        # Memory
        self.mem_pct  = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.swap_pct = deque([0.0] * HISTORY, maxlen=HISTORY)

        # Network (delta rates in bytes/sec)
        _net = psutil.net_io_counters()
        self._net_sent = _net.bytes_sent
        self._net_recv = _net.bytes_recv
        self.net_up   = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.net_down = deque([0.0] * HISTORY, maxlen=HISTORY)

        # Disk I/O (delta rates in bytes/sec)
        try:
            _d = psutil.disk_io_counters()
            self._drb = _d.read_bytes  if _d else 0
            self._dwb = _d.write_bytes if _d else 0
        except Exception:
            self._drb = self._dwb = 0
        self.disk_r = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.disk_w = deque([0.0] * HISTORY, maxlen=HISTORY)

        # Meta
        self.boot_time  = datetime.fromtimestamp(psutil.boot_time())
        self.start_time = datetime.now()
        self.tick       = 0
        self.alerts: list[Alert] = []

        # Warm-up: first cpu_percent() always returns 0
        psutil.cpu_percent(percpu=True)

    # ── public ────────────────────────────────────────────────────────────────

    def update(self) -> None:
        self.tick += 1
        self._sample_cpu()
        self._sample_memory()
        self._sample_network()
        self._sample_disk()

    # ── private sampling ──────────────────────────────────────────────────────

    def _sample_cpu(self) -> None:
        per   = psutil.cpu_percent(percpu=True)
        total = sum(per) / max(len(per), 1)
        self.cpu_total.append(total)
        for i, p in enumerate(per):
            if i < self.n_cpu:
                self.cpu_cores[i].append(p)
            if p >= 95:
                self._alert("crit", f"Core {i} at {p:.0f}%")
            elif p >= 85:
                self._alert("warn", f"Core {i} spiked to {p:.0f}%")

    def _sample_memory(self) -> None:
        mem  = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.mem_pct.append(mem.percent)
        self.swap_pct.append(swap.percent)
        if mem.percent  >= 95: self._alert("crit", f"RAM critical: {mem.percent:.0f}%")
        if swap.percent >= 85: self._alert("warn", f"Swap pressure: {swap.percent:.0f}%")

    def _sample_network(self) -> None:
        net = psutil.net_io_counters()
        self.net_up.append((net.bytes_sent - self._net_sent) / REFRESH)
        self.net_down.append((net.bytes_recv - self._net_recv) / REFRESH)
        self._net_sent = net.bytes_sent
        self._net_recv = net.bytes_recv

    def _sample_disk(self) -> None:
        try:
            d = psutil.disk_io_counters()
            if d:
                self.disk_r.append((d.read_bytes  - self._drb) / REFRESH)
                self.disk_w.append((d.write_bytes - self._dwb) / REFRESH)
                self._drb = d.read_bytes
                self._dwb = d.write_bytes
                return
        except Exception:
            pass
        self.disk_r.append(0.0)
        self.disk_w.append(0.0)

    def _alert(self, level: str, msg: str) -> None:
        # Suppress identical consecutive alerts
        if self.alerts and self.alerts[-1].message == msg:
            return
        self.alerts.append(Alert(datetime.now(), level, msg))
        if len(self.alerts) > 40:
            self.alerts.pop(0)
