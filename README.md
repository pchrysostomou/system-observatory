# 🔭 System Observatory

**Real-time system monitoring dashboard with a beautiful glassmorphic UI.**

A full-stack web dashboard for continuous system observation — live metrics, custom alerts, process management, historical data analysis, and persistent SQLite storage.

![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-00ff41?style=flat-square)
![Type: Full Stack](https://img.shields.io/badge/Type-Full%20Stack-00d4ff?style=flat-square)
![Real-time: SSE](https://img.shields.io/badge/Real--time-SSE-00ff41?style=flat-square)
![Database: SQLite](https://img.shields.io/badge/Database-SQLite-0066cc?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

### 📊 Real-Time System Monitoring
- **6 Live Charts** — CPU, Memory, Swap, Network (up/down), Disk I/O
- **Per-Core CPU Tracking** — Individual core usage monitoring
- **Animated Health Score** — 0-100 dial with auto-detection
- **Server-Sent Events** — Real-time streaming, no polling overhead
- **120-Second Rolling History** — Charts pre-populated from DB on startup

### 💾 Historical Data & Analytics
- **SQLite Storage** — Persistent 24/7 metrics collection
- **Instant Chart Warm-up** — Charts fill with real history on every page load
- **Time Range Views** — 24h, 7d, 30d aggregated statistics
- **CSV Export** — Download metrics for external analysis
- **Auto-Cleanup** — Automatic removal of old records

### ⚠️ Smart Alert System
- **Custom Thresholds** — Set CPU, Memory, Disk limits
- **Browser Notifications** — Native OS alerts when triggered
- **Sound Alerts** — Audio beep for critical events
- **Persistent Settings** — localStorage configuration
- **Alert History** — Track all triggered alerts

### ⚙️ Process Management
- **Top Process Ranking** — Sorted by resource usage, all edge cases handled
- **Process Details** — CPU%, memory, threads, status, uptime
- **Process Control** — Kill/terminate processes safely

### 🌐 Network & Disk Intelligence
- **Network Interface Monitoring** — IP, speed, UP/DOWN status
- **I/O Rate Tracking** — Real-time read/write speeds (MB/s)
- **Partition Breakdown** — All mounted drives with usage %
- **Traffic Totals** — Cumulative bytes sent/received

### 🎨 Beautiful UI
- **Glassmorphism Design** — Frosted glass with backdrop blur
- **Dark/Light Themes** — Toggle anytime, persisted across sessions
- **Smooth Animations** — Slide-ins, pulses, gradients
- **Responsive Layout** — Mobile, tablet, desktop support
- **Keyboard Shortcuts** — Quick access (?, T, S, E, B, R)

### ⚡ Performance & Benchmarking
- **System Benchmarks** — CPU, Memory, Disk performance tests
- **Reboot Checks** — Detect if system needs a restart
- **Resource Optimization** — Cleanup recommendations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or 3.12 (recommended)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
git clone https://github.com/pchrysostomou/system-observatory.git
cd system-observatory
pip install -r requirements.txt
```

### Run

```bash
python3 app.py
```

Then open **http://localhost:8080** in your browser.

Or use the startup script:
```bash
./run.sh
```

> **Note:** If `python3` doesn't have `psutil`/`flask` installed, try `python3.12 app.py` explicitly.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `?` | Help & shortcuts guide |
| `T` | Toggle theme (dark/light) |
| `S` | Settings & alert configuration |
| `E` | Export metrics to CSV |
| `B` | Run system benchmarks |
| `R` | Refresh dashboard |

---

## 📊 Dashboard Overview

### Header
- **Live Clock** — Real-time HH:MM:SS
- **Theme Toggle** — 🌙/☀️ dark/light mode
- **Settings** — ⚙️ alert configuration
- **Help** — ❓ keyboard shortcuts
- **Health Badge** — Animated system status indicator

### Real-Time Charts
1. **CPU Usage** — Total % with 120s rolling history
2. **Memory & Swap** — Doughnut charts with GB breakdown
3. **Network Traffic** — Upload/Download rates with trends
4. **Disk I/O** — Read/Write speeds in MB/s

### Data Tables
- **Top Processes** — CPU%, memory%, status
- **Network Interfaces** — IP address, speed, connectivity
- **Disk Partitions** — Mount points, filesystem, usage, free space

---

## 📁 Project Structure

```
system-observatory/
├── app.py                  # Flask backend + metrics collector
├── database.py             # SQLite storage & queries
├── sysmon.py               # Bonus: terminal-based monitor
├── run.sh                  # Startup script
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Dashboard HTML
└── static/
    ├── css/style.css        # Glassmorphism styling
    └── js/app.js            # Real-time frontend (Chart.js)
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/snapshot` | GET | Current metrics snapshot |
| `/api/stream` | GET | Server-Sent Events stream |
| `/api/historical?hours=24` | GET | Historical metrics |
| `/api/export?hours=24` | GET | CSV download |
| `/api/processes` | GET | Top 15 processes by CPU |
| `/api/network-interfaces` | GET | Network interface details |
| `/api/disk-partitions` | GET | Disk partition info |
| `/api/health` | GET | Health score & issues |
| `/api/benchmark` | POST | Run system benchmarks |
| `/api/process/kill` | POST | Terminate a process |
| `/api/process/info/<pid>` | GET | Detailed process info |
| `/api/system/reboot-needed` | GET | Check if reboot needed |

---

## 🛠️ Technical Stack

### Backend
- **Flask 3.0** — Lightweight web framework
- **psutil** — System metrics collection
- **SQLite3** — Persistent data storage (built into Python, no install needed)
- **Server-Sent Events (SSE)** — Real-time streaming
- **Threading** — Background metric collection

### Frontend
- **Chart.js 4.4** — Interactive real-time charts
- **Vanilla JavaScript** — No frameworks, fast and lightweight
- **CSS3** — Glassmorphism, animations, grid layout
- **EventSource API** — SSE client
- **Web Audio API** — Sound notifications
- **Notification API** — Browser alerts

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Update Frequency** | 1 second |
| **Chart History** | 120 seconds |
| **Database Storage** | Every 10 seconds |
| **Protocol** | Server-Sent Events (SSE) |
| **Memory Usage** | ~50 MB |
| **CPU Impact** | < 5% |

---

## 🔧 Configuration

### Change Port
Edit `app.py`:
```python
app.run(debug=True, host='localhost', port=8000)
```

### Update Frequency
```python
time.sleep(1)  # Change to 0.5 for faster updates
```

### Custom Alerts
Open the Settings modal in the dashboard (press `S`).

### Color Scheme
Edit `static/css/style.css`:
```css
:root {
    --primary: #00d4ff;
    --accent: #ff006e;
}
```

---

## 📦 Dependencies

```
Flask==3.0.0
Flask-CORS==4.0.0
psutil==5.9.6
Werkzeug==3.0.1
```

SQLite3 is built into Python — no separate database install required.

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -i :8080
# Then change port in app.py
```

### Charts Not Showing
- Charts pre-populate from SQLite on startup; they fill with live data within seconds if the DB is empty
- Check browser console (F12) for errors
- Ensure `/api/stream` is accessible
- Refresh with `R`

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### Database Locked
- Ensure only one Flask instance is running
- Delete `metrics.db` to reset all historical data

---

## 🌟 Bonus: Terminal Monitor

**sysmon.py** — A terminal-based system monitor with Unicode sparklines.

```bash
python3 sysmon.py
```

Features: CPU, memory, network, disk stats with block sparklines (▁▂▃▄▅▆▇█), per-core visualization, and color-coded gauges.

---
**System Observatory — Continuously Observing Your System** 🔭
