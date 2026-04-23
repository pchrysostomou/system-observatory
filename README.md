# 🔭 System Observatory

**Real-time system monitoring dashboard with AI-powered UI/UX design intelligence.**

A beautiful glassmorphic web dashboard for continuous system observation, featuring live metrics, custom alerts, process management, historical data analysis, and professional design system generation tools.

![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-00ff41?style=flat-square&logo=checkmark)
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
- **Server-Sent Events** — Real-time streaming (no polling overhead)
- **120-Second History** — Rolling window sparklines

### 💾 Historical Data & Analytics
- **SQLite Storage** — Persistent 24/7 metrics collection
- **Time Range Views** — 24h, 7d, 30d aggregated statistics
- **Trend Analysis** — Identify patterns and performance spikes
- **CSV Export** — Download metrics for external analysis
- **Auto-Cleanup** — Automatic old data removal

### ⚠️ Smart Alert System
- **Custom Thresholds** — Set CPU, Memory, Disk limits
- **Browser Notifications** — Native OS alerts when triggered
- **Sound Alerts** — Audio beep for critical events
- **Persistent Settings** — localStorage configuration
- **Alert History** — Track all triggered alerts

### ⚙️ Process Management
- **Process Control** — Kill/terminate processes safely
- **Process Details** — CPU%, memory, threads, status, uptime
- **Process Search** — Find and manage any process
- **Top Process Ranking** — Sorted by resource usage

### 🌐 Network & Disk Intelligence
- **Network Interface Monitoring** — IP, speed, UP/DOWN status
- **I/O Rate Tracking** — Real-time read/write speeds (MB/s)
- **Partition Breakdown** — All mounted drives with usage %
- **Traffic Totals** — Cumulative bytes sent/received

### 🎨 Beautiful UI & Design Tools
- **Glassmorphism Design** — Frosted glass with backdrop blur
- **Dark/Light Themes** — Toggle anytime, persisted
- **Smooth Animations** — Slide-ins, pulses, gradients
- **Responsive Layout** — Mobile, tablet, desktop support
- **Keyboard Shortcuts** — Quick access (?, T, S, E, B, R)
- **Design System Generator** — AI-powered UI/UX tools

### ⚡ Performance & Benchmarking
- **System Benchmarks** — CPU, Memory, Disk performance tests
- **Reboot Checks** — Detect if system needs restart
- **Resource Optimization** — Recommendations for cleanup

---

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
cd system-observatory
pip install -r requirements.txt
```

### Run

```bash
python3 app.py
```

Then open: **http://localhost:8080** in your browser

Or use the startup script:
```bash
./run.sh
```

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

### Header Section
- **Live Clock** — Real-time HH:MM:SS
- **Theme Toggle** — 🌙/☀️ for dark/light mode
- **Settings Button** — ⚙️ for configuration
- **Help Button** — ❓ for keyboard shortcuts
- **Health Badge** — Animated indicator of system status

### System Overview Cards
- **Health Score Dial** — 0-100 animated gauge
- **System Info** — Hostname, OS, uptime, process count
- **Quick Stats** — CPU frequency, core count

### Real-Time Charts
1. **CPU Usage** — Total % with 120s history
2. **Memory & Swap** — Doughnut charts with GB breakdown
3. **Network Traffic** — Upload/Download rates with trends
4. **Disk I/O** — Read/Write speeds in MB/s

### Detailed Metrics Grid
- Per-core CPU breakdown
- Memory: Used, Total, Available
- Network: Upload, Download, Totals
- Disk: Usage %, Read/Write rates

### Data Tables
- **Top Processes** — By CPU%, with memory% and status
- **Network Interfaces** — IP address, speed, connectivity status
- **Disk Partitions** — Mount points, filesystem, usage, free space

### Settings Modal
- ✅ Custom alert thresholds
- ✅ Enable/disable notifications
- ✅ Sound on/off toggle
- ✅ Export metrics to CSV
- ✅ Run system benchmarks

---

## 📁 Project Structure

```
system-observatory/
├── 🚀 run.sh                      # Startup script
├── 🐍 app.py                      # Flask backend (400+ lines)
├── 💾 database.py                 # SQLite utilities (80+ lines)
├── 🖥️  sysmon.py                  # Terminal monitor (bonus)
├── 📋 requirements.txt            # Python dependencies
├── 📖 README.md                   # This file
├── .gitignore                     # Git ignore rules
├── templates/
│   └── 📄 index.html              # Dashboard HTML (400+ lines)
└── static/
    ├── css/
    │   └── 🎨 style.css           # Glassmorphism styling (800+ lines)
    └── js/
        └── ⚡ app.js              # Real-time frontend (900+ lines)
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/snapshot` | GET | Current metrics snapshot |
| `/api/stream` | GET | Server-Sent Events stream |
| `/api/historical?hours=24` | GET | Historical metrics (24h, 7d, 30d) |
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

## 🎨 Design System

### Color Palette
```
Primary:    #00d4ff (Cyan)
Accent:     #ff006e (Magenta)
Success:    #00ff41 (Neon Green)
Warning:    #ffb700 (Orange)
Danger:     #ff006e (Red/Magenta)
Background: Dark navy (#0a0e27, #050811)
Text:       Light (#e0e6ff, #8a96c0)
```

### Visual Effects
- **Backdrop Blur**: 10px (header), 20px (cards)
- **Glassmorphism**: RGBA surfaces (0.4-0.8 opacity)
- **Border Radius**: 16px cards, 8px elements
- **Shadow**: 0 8px 32px rgba(0,0,0,0.3)
- **Animations**: Smooth easing, 60fps updates

### Responsive Breakpoints
- **Desktop**: Full layout with all details
- **Tablet**: Adapted grid, compact tables
- **Mobile**: Stacked layout, touch-friendly

---

## 🛠️ Technical Stack

### Backend
- **Flask 3.0** — Lightweight web framework
- **psutil 5.9** — System metrics collection
- **SQLite3** — Persistent data storage
- **Server-Sent Events (SSE)** — Real-time streaming
- **Threading** — Background metric collection

### Frontend
- **HTML5** — Semantic markup
- **CSS3** — Glassmorphism, animations, grid layout
- **Chart.js 4.4** — Interactive real-time charts
- **Vanilla JavaScript** — No frameworks (fast & lightweight)
- **EventSource API** — SSE client
- **Web Audio API** — Sound notifications
- **Notification API** — Browser alerts

### Database
- **SQLite3** — Zero-config embedded database
- **Thread-safe operations** — Safe concurrent access
- **24-hour auto-cleanup** — Delete old metrics
- **Indexed queries** — Fast timestamp lookups

---

## 📈 Performance Specs

| Metric | Value |
|--------|-------|
| **Update Frequency** | 1 second (configurable) |
| **Chart History** | 120 seconds |
| **Database Storage** | Every 10 seconds |
| **Network Protocol** | Server-Sent Events (SSE) |
| **Browser Updates** | Only changed data (minimal DOM manipulation) |
| **Bundle Size** | ~150 KB (HTML+CSS+JS combined) |
| **Memory Usage** | ~50 MB (metrics in memory) |
| **CPU Impact** | < 5% (background collection) |

---

## 🔧 Configuration

### Change Port
Edit `app.py`:
```python
app.run(debug=True, host='localhost', port=8000)  # Change from 8080
```

### Update Frequency
Backend (`app.py`):
```python
time.sleep(1)  # Change to 0.5 for faster updates
```

### Alert Thresholds
Settings Modal (in dashboard) → Configure CPU, Memory, Disk limits

### Color Scheme
Edit `static/css/style.css`:
```css
:root {
    --primary: #00d4ff;
    --accent: #ff006e;
    /* ... */
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

**No frontend dependencies** — Pure HTML, CSS, JavaScript

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -i :8080
# Then change port in app.py
```

### High CPU Usage
- Reduce update frequency in `app.py`
- Close other browser tabs
- Check process table for resource hogs

### Charts Not Updating
- Check browser console (F12) for errors
- Ensure `/api/stream` is accessible
- Try refreshing the page (R key)

### Database Locked
- Ensure only one Flask instance running
- Check `/tmp/app.log` for errors
- Delete `metrics.db` to reset

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

---

## 🌟 Bonus: Terminal Monitor

Included: **sysmon.py** — Beautiful terminal-based system monitor with Unicode sparklines.

```bash
python3 sysmon.py
```

Features:
- Real-time CPU, memory, network, disk stats
- Unicode block sparklines (▁▂▃▄▅▆▇█)
- Per-core CPU visualization
- Process ranking by CPU usage
- Network interface breakdown
- Color-coded gauges and alerts

---

## 💡 Pro Tips

1. **Keyboard Shortcuts** — Press `?` to see all shortcuts
2. **Custom Alerts** — Set thresholds in Settings (S key)
3. **Export Data** — Download CSV for analysis (E key)
4. **Benchmarking** — Run tests to measure system (B key)
5. **Dark Mode** — Easy on the eyes, press T key
6. **Process Details** — Click any process in the table
7. **Theme Persistence** — Your theme choice is saved

---

## 📊 Use Cases

**System Administrators:**
- Monitor server resources 24/7
- Detect performance issues early
- Track historical trends
- Export reports for analysis

**DevOps Engineers:**
- Real-time performance monitoring
- Benchmark system capabilities
- Manage runaway processes
- Identify optimization opportunities

**Developers:**
- Monitor app performance impact
- Debug resource leaks
- Benchmark code changes
- Track system health

**Designers/UI/UX:**
- Use design system generator
- Create beautiful UI components
- Get typography & color recommendations
- Generate design systems automatically

---

## 📄 License

MIT License — Free to use, modify, and distribute.

See LICENSE file for details.

---

## 🙌 Built With

- **Flask** — Micro web framework
- **psutil** — System & process utilities
- **Chart.js** — Beautiful interactive charts
- **SQLite** — Embedded database
- **Server-Sent Events** — Real-time streaming
- **Glassmorphism** — Modern design pattern
- **Cyberpunk Aesthetic** — Color scheme inspiration

---

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/pchrysostomou/system-observatory.git
cd system-observatory

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python3 app.py

# Open in browser
# http://localhost:8080
```

---

**System Observatory — Continuously Observing Your System** 🔭✨

Open http://localhost:8080 and start monitoring! 🚀
