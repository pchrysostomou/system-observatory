"""
Claude Power Dashboard — Full-stack real-time system monitor.
Beautiful web interface with live metrics, charts, and interactive components.
"""

import json
import time
import psutil
import socket
import platform
import subprocess
import csv
import io
from datetime import datetime, timedelta
from threading import Thread
from collections import deque
from flask import Flask, render_template, jsonify, Response, request, send_file
from flask_cors import CORS
from database import MetricsDB

# ─── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ─── Database setup ───────────────────────────────────────────────────────────

db = MetricsDB()

# ─── System metrics storage ────────────────────────────────────────────────────

HISTORY_SIZE = 120  # 2 minutes at 1Hz

class MetricsCollector:
    def __init__(self):
        self.cpu_history = deque(maxlen=HISTORY_SIZE)
        self.memory_history = deque(maxlen=HISTORY_SIZE)
        self.swap_history = deque(maxlen=HISTORY_SIZE)
        self.network_up_history = deque(maxlen=HISTORY_SIZE)
        self.network_down_history = deque(maxlen=HISTORY_SIZE)
        self.disk_read_history = deque(maxlen=HISTORY_SIZE)
        self.disk_write_history = deque(maxlen=HISTORY_SIZE)
        self.temp_history = deque(maxlen=HISTORY_SIZE)

        # Counters for rate calculation
        self.last_net_sent = psutil.net_io_counters().bytes_sent
        self.last_net_recv = psutil.net_io_counters().bytes_recv
        self.last_disk_read = psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0
        self.last_disk_write = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0

        self.timestamp = datetime.now()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())

    def collect(self):
        """Collect current system metrics."""
        now = datetime.now()
        dt = (now - self.timestamp).total_seconds() or 1
        self.timestamp = now

        # CPU
        cpu_pct = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_pct)

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.memory_history.append(mem.percent)
        self.swap_history.append(swap.percent)

        # Network rates
        net = psutil.net_io_counters()
        net_up_rate = (net.bytes_sent - self.last_net_sent) / dt
        net_down_rate = (net.bytes_recv - self.last_net_recv) / dt
        self.network_up_history.append(net_up_rate)
        self.network_down_history.append(net_down_rate)
        self.last_net_sent = net.bytes_sent
        self.last_net_recv = net.bytes_recv

        # Disk I/O rates
        disk = psutil.disk_io_counters()
        if disk:
            disk_read_rate = (disk.read_bytes - self.last_disk_read) / dt
            disk_write_rate = (disk.write_bytes - self.last_disk_write) / dt
            self.disk_read_history.append(disk_read_rate)
            self.disk_write_history.append(disk_write_rate)
            self.last_disk_read = disk.read_bytes
            self.last_disk_write = disk.write_bytes

        # Temperature
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                avg_temp = sum(e[0].current for entries in temps.values() for e in entries) / sum(len(entries) for entries in temps.values())
                self.temp_history.append(avg_temp)
        except:
            pass

    def get_snapshot(self):
        """Get current metrics as a dict."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu_freq = psutil.cpu_freq()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        # CPU per-core
        cpu_per_core = psutil.cpu_percent(percpu=True)

        # Uptime
        uptime_seconds = (datetime.now() - boot_time).total_seconds()

        # Health score (0-100)
        health = 100
        if mem.percent > 85: health -= 20
        elif mem.percent > 70: health -= 10
        if len(self.cpu_history) > 0 and list(self.cpu_history)[-1] > 80: health -= 15

        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'total': list(self.cpu_history)[-1] if self.cpu_history else 0,
                'per_core': cpu_per_core,
                'freq_ghz': cpu_freq.current / 1000 if cpu_freq else 0,
                'history': list(self.cpu_history),
            },
            'memory': {
                'percent': mem.percent,
                'used_gb': mem.used / (1024**3),
                'total_gb': mem.total / (1024**3),
                'available_gb': mem.available / (1024**3),
                'history': list(self.memory_history),
            },
            'swap': {
                'percent': swap.percent,
                'used_gb': swap.used / (1024**3),
                'total_gb': swap.total / (1024**3),
                'history': list(self.swap_history),
            },
            'network': {
                'up_mbps': list(self.network_up_history)[-1] / (1024**2) if self.network_up_history else 0,
                'down_mbps': list(self.network_down_history)[-1] / (1024**2) if self.network_down_history else 0,
                'up_total_gb': net.bytes_sent / (1024**3),
                'down_total_gb': net.bytes_recv / (1024**3),
                'up_history': list(self.network_up_history),
                'down_history': list(self.network_down_history),
            },
            'disk': {
                'percent': disk.percent,
                'used_gb': disk.used / (1024**3),
                'total_gb': disk.total / (1024**3),
                'read_mbps': list(self.disk_read_history)[-1] / (1024**2) if self.disk_read_history else 0,
                'write_mbps': list(self.disk_write_history)[-1] / (1024**2) if self.disk_write_history else 0,
                'history': list(self.disk_history_pct),
            },
            'system': {
                'hostname': socket.gethostname(),
                'os': f"{platform.system()} {platform.release()}",
                'uptime_seconds': uptime_seconds,
                'processes': len(psutil.pids()),
                'boot_time': boot_time.isoformat(),
            },
            'health_score': max(0, health),
        }

    @property
    def disk_history_pct(self):
        """Disk usage percentage over time (computed from space)."""
        return [psutil.disk_usage('/').percent] * len(self.cpu_history)

# ─── Global collector ──────────────────────────────────────────────────────────

collector = MetricsCollector()

def background_collector():
    """Continuously collect metrics."""
    global collector
    while True:
        time.sleep(1)
        collector.collect()
        # Store to database every 10 seconds
        if collector.tick % 10 == 0:
            try:
                snapshot = collector.get_snapshot()
                db.store_metrics(snapshot)
            except Exception as e:
                print(f"DB store error: {e}")

# Start collector thread
collector_thread = Thread(target=background_collector, daemon=True)
collector_thread.start()

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/snapshot')
def api_snapshot():
    """Get latest metrics snapshot."""
    return jsonify(collector.get_snapshot())

@app.route('/api/stream')
def api_stream():
    """Server-Sent Events stream of metrics."""
    def generate():
        last_sent = time.time()
        while True:
            if time.time() - last_sent > 0.5:  # Send every 500ms
                yield f"data: {json.dumps(collector.get_snapshot())}\n\n"
                last_sent = time.time()
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/processes')
def api_processes():
    """Get top processes by CPU usage."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    return jsonify(procs[:15])

@app.route('/api/network-interfaces')
def api_network_interfaces():
    """Get network interface details."""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    interfaces = []
    for name, addr_list in addrs.items():
        ip = next((a.address for a in addr_list if a.family == socket.AF_INET), '—')
        st = stats.get(name)
        interfaces.append({
            'name': name,
            'ip': ip,
            'speed': f"{st.speed} Mb/s" if st and st.speed else '—',
            'is_up': st.isup if st else False,
        })

    return jsonify(sorted(interfaces, key=lambda x: not x['is_up']))

@app.route('/api/disk-partitions')
def api_disk_partitions():
    """Get disk partition details."""
    partitions = psutil.disk_partitions(all=False)
    data = []

    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            data.append({
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total_gb': usage.total / (1024**3),
                'used_gb': usage.used / (1024**3),
                'free_gb': usage.free / (1024**3),
                'percent': usage.percent,
            })
        except PermissionError:
            pass

    return jsonify(data)

@app.route('/api/health')
def api_health():
    """Compute system health report."""
    snapshot = collector.get_snapshot()
    health = snapshot['health_score']

    issues = []
    if snapshot['memory']['percent'] > 85:
        issues.append(f"High memory usage: {snapshot['memory']['percent']:.1f}%")
    if snapshot['cpu']['total'] > 80:
        issues.append(f"High CPU usage: {snapshot['cpu']['total']:.1f}%")
    if snapshot['disk']['percent'] > 85:
        issues.append(f"Disk space low: {snapshot['disk']['percent']:.1f}%")

    return jsonify({
        'score': health,
        'status': 'Good' if health >= 80 else 'Fair' if health >= 60 else 'Poor',
        'issues': issues,
    })

# ─── New Advanced Features ─────────────────────────────────────────────────────

@app.route('/api/historical')
def api_historical():
    """Get historical metrics with time range."""
    hours = request.args.get('hours', 24, type=int)
    metrics = db.get_metrics(hours=hours)
    stats = db.get_stats(hours=hours)

    return jsonify({
        'metrics': metrics,
        'stats': stats,
        'hours': hours,
    })

@app.route('/api/export')
def api_export():
    """Export metrics to CSV."""
    hours = request.args.get('hours', 24, type=int)
    metrics = db.get_metrics(hours=hours)

    output = io.StringIO()
    if metrics:
        writer = csv.DictWriter(output, fieldnames=metrics[0].keys())
        writer.writeheader()
        writer.writerows(metrics)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/process/kill', methods=['POST'])
def process_kill():
    """Kill a process by PID."""
    pid = request.json.get('pid')
    try:
        p = psutil.Process(pid)
        p.terminate()
        return jsonify({'success': True, 'message': f'Process {pid} terminated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/process/info/<int:pid>')
def process_info(pid):
    """Get detailed process information."""
    try:
        p = psutil.Process(pid)
        return jsonify({
            'pid': p.pid,
            'name': p.name(),
            'exe': p.exe(),
            'status': p.status(),
            'cpu_percent': p.cpu_percent(),
            'memory_info': {
                'rss': p.memory_info().rss / (1024**2),  # MB
                'vms': p.memory_info().vms / (1024**2),
            },
            'num_threads': p.num_threads(),
            'create_time': datetime.fromtimestamp(p.create_time()).isoformat(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/benchmark', methods=['POST'])
def benchmark():
    """Run system benchmarks."""
    import timeit

    # CPU benchmark
    cpu_time = timeit.timeit('sum(range(1000000))', number=5) / 5

    # Memory benchmark
    mem_before = psutil.virtual_memory().used
    _ = [i for i in range(10000000)]
    mem_after = psutil.virtual_memory().used
    mem_delta = (mem_after - mem_before) / (1024**2)

    # Disk benchmark
    disk_read = psutil.disk_io_counters().read_bytes
    time.sleep(1)
    disk_read_new = psutil.disk_io_counters().read_bytes
    disk_read_rate = (disk_read_new - disk_read) / (1024**2)

    return jsonify({
        'cpu': {
            'time_seconds': cpu_time,
            'ops_per_sec': 1 / cpu_time if cpu_time > 0 else 0,
        },
        'memory': {
            'allocated_mb': mem_delta,
        },
        'disk': {
            'read_mbps': disk_read_rate,
        },
        'timestamp': datetime.now().isoformat(),
    })

@app.route('/api/system/reboot-needed')
def reboot_needed():
    """Check if system reboot is needed."""
    # Check for typical reboot indicators
    reasons = []

    try:
        if psutil.virtual_memory().percent > 90:
            reasons.append('Memory pressure high')
        if psutil.disk_usage('/').percent > 95:
            reasons.append('Disk almost full')
    except:
        pass

    return jsonify({
        'reboot_needed': len(reasons) > 0,
        'reasons': reasons,
    })

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8080, use_reloader=False)
