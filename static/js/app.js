/* ──────────────────────────────────────────────────────────────────────────────
   Claude Power Dashboard — Real-time Frontend
   ────────────────────────────────────────────────────────────────────────────── */

// ─── Theme Management ─────────────────────────────────────────────────────────

function initTheme() {
    const theme = localStorage.getItem('theme') || 'dark';
    applyTheme(theme);
}

function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'light') {
        html.style.setProperty('--bg-dark', '#f5f5f5');
        html.style.setProperty('--bg-darker', '#ececec');
        html.style.setProperty('--text-primary', '#1a1a1a');
        html.style.setProperty('--text-secondary', '#555555');
        html.style.setProperty('--surface', 'rgba(255, 255, 255, 0.7)');
        html.style.setProperty('--glass-bg', 'rgba(255, 255, 255, 0.4)');
        document.getElementById('themeToggle').textContent = '☀️';
    } else {
        html.style.setProperty('--bg-dark', '#0a0e27');
        html.style.setProperty('--bg-darker', '#050811');
        html.style.setProperty('--text-primary', '#e0e6ff');
        html.style.setProperty('--text-secondary', '#8a96c0');
        html.style.setProperty('--surface', 'rgba(20, 26, 50, 0.8)');
        html.style.setProperty('--glass-bg', 'rgba(20, 26, 50, 0.4)');
        document.getElementById('themeToggle').textContent = '🌙';
    }
    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    const current = localStorage.getItem('theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
}

// ─── Settings & Alerts ────────────────────────────────────────────────────────

let alerts = {
    cpu: { enabled: false, threshold: 80 },
    memory: { enabled: false, threshold: 85 },
    disk: { enabled: false, threshold: 90 },
    soundEnabled: true,
};

function loadSettings() {
    const saved = localStorage.getItem('alerts');
    if (saved) {
        alerts = JSON.parse(saved);
        document.getElementById('cpuAlert').checked = alerts.cpu.enabled;
        document.getElementById('cpuThreshold').value = alerts.cpu.threshold;
        document.getElementById('memAlert').checked = alerts.memory.enabled;
        document.getElementById('memThreshold').value = alerts.memory.threshold;
        document.getElementById('diskAlert').checked = alerts.disk.enabled;
        document.getElementById('diskThreshold').value = alerts.disk.threshold;
        document.getElementById('soundEnabled').checked = alerts.soundEnabled;
    }
}

function saveSettings() {
    alerts.cpu.enabled = document.getElementById('cpuAlert').checked;
    alerts.cpu.threshold = parseFloat(document.getElementById('cpuThreshold').value);
    alerts.memory.enabled = document.getElementById('memAlert').checked;
    alerts.memory.threshold = parseFloat(document.getElementById('memThreshold').value);
    alerts.disk.enabled = document.getElementById('diskAlert').checked;
    alerts.disk.threshold = parseFloat(document.getElementById('diskThreshold').value);
    alerts.soundEnabled = document.getElementById('soundEnabled').checked;
    localStorage.setItem('alerts', JSON.stringify(alerts));
}

function checkAlerts(data) {
    if (alerts.cpu.enabled && data.cpu.total > alerts.cpu.threshold) {
        showAlert(`🔴 CPU High: ${data.cpu.total.toFixed(1)}% (threshold: ${alerts.cpu.threshold}%)`);
    }
    if (alerts.memory.enabled && data.memory.percent > alerts.memory.threshold) {
        showAlert(`🔴 Memory High: ${data.memory.percent.toFixed(1)}% (threshold: ${alerts.memory.threshold}%)`);
    }
    if (alerts.disk.enabled && data.disk.percent > alerts.disk.threshold) {
        showAlert(`🔴 Disk High: ${data.disk.percent.toFixed(1)}% (threshold: ${alerts.disk.threshold}%)`);
    }
}

function showAlert(message) {
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Claude Power Alert', { body: message });
    }
    // Sound
    if (alerts.soundEnabled) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
}

// ─── Export functionality ──────────────────────────────────────────────────────

async function exportMetrics() {
    try {
        const response = await fetch('/api/export?hours=24');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `metrics_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Export failed:', e);
        alert('Export failed');
    }
}

// ─── Benchmarking ─────────────────────────────────────────────────────────────

async function runBenchmark() {
    const resultsDiv = document.getElementById('benchmarkResults');
    resultsDiv.textContent = '⚡ Running benchmark...';
    resultsDiv.classList.add('active');

    try {
        const response = await fetch('/api/benchmark', { method: 'POST' });
        const data = await response.json();

        let html = '<strong>Benchmark Results:</strong><br>';
        html += `CPU Time: ${data.cpu.time_seconds.toFixed(4)}s<br>`;
        html += `CPU Ops/sec: ${data.cpu.ops_per_sec.toFixed(0)}<br>`;
        html += `Memory Allocated: ${data.memory.allocated_mb.toFixed(2)}MB<br>`;
        html += `Disk Read: ${data.disk.read_mbps.toFixed(2)}MB/s<br>`;
        resultsDiv.innerHTML = html;
    } catch (e) {
        resultsDiv.innerHTML = '❌ Benchmark failed';
        console.error(e);
    }
}

// ─── Modal Management ──────────────────────────────────────────────────────────

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => {
    // Theme
    initTheme();
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);

    // Settings
    document.getElementById('settingsBtn').addEventListener('click', () => {
        loadSettings();
        openModal('settingsModal');
    });
    document.getElementById('settingsClose').addEventListener('click', () => {
        saveSettings();
        closeModal('settingsModal');
    });

    // Help
    document.getElementById('helpBtn').addEventListener('click', () => openModal('helpModal'));
    document.getElementById('helpClose').addEventListener('click', () => closeModal('helpModal'));

    // Export & Benchmark
    document.getElementById('exportBtn').addEventListener('click', exportMetrics);
    document.getElementById('benchmarkBtn').addEventListener('click', runBenchmark);

    // Close modals on background click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

let charts = {};

// ─── Format helpers ───────────────────────────────────────────────────────────

function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

function formatPercent(pct) {
    return pct.toFixed(1) + '%';
}

function formatMbps(bps) {
    return (bps / (1024 * 1024)).toFixed(2) + ' Mbps';
}

// ─── Color utilities ──────────────────────────────────────────────────────────

function getHealthColor(score) {
    if (score >= 80) return '#00ff41';
    if (score >= 60) return '#ffb700';
    return '#ff006e';
}

function getMetricColor(percent) {
    if (percent >= 85) return 'rgb(255, 0, 110)';
    if (percent >= 70) return 'rgb(255, 183, 0)';
    return 'rgb(0, 255, 65)';
}

function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

// ─── Chart configuration ──────────────────────────────────────────────────────

function createChartOptions(title, yMax = 100) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        interaction: {
            intersect: false,
            mode: 'index',
        },
        plugins: {
            legend: {
                display: false,
            },
            title: {
                display: false,
            },
            filler: true,
        },
        scales: {
            y: {
                beginAtZero: true,
                max: yMax,
                ticks: {
                    color: '#8a96c0',
                    font: { size: 11 },
                },
                grid: {
                    color: 'rgba(0, 212, 255, 0.05)',
                    borderColor: 'rgba(0, 212, 255, 0.1)',
                },
            },
            x: {
                ticks: {
                    color: '#8a96c0',
                    font: { size: 11 },
                },
                grid: {
                    color: 'rgba(0, 212, 255, 0.05)',
                    borderColor: 'rgba(0, 212, 255, 0.1)',
                },
            },
        },
    };
}

// ─── Initialize charts ────────────────────────────────────────────────────────

function initCharts() {
    const chartConfigs = {
        cpuChart: {
            type: 'line',
            data: {
                labels: Array(120).fill(''),
                datasets: [{
                    label: 'CPU %',
                    data: Array(120).fill(0),
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: true,
                    cubicInterpolationMode: 'monotone',
                }],
            },
            options: createChartOptions('CPU Usage', 100),
        },
        memoryChart: {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [50, 50],
                    backgroundColor: [
                        'rgba(255, 0, 110, 0.7)',
                        'rgba(0, 212, 255, 0.2)',
                    ],
                    borderColor: [
                        'rgba(255, 0, 110, 1)',
                        'rgba(0, 212, 255, 0.5)',
                    ],
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e0e6ff',
                            font: { size: 12, weight: 500 },
                            padding: 15,
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' GB';
                            },
                        },
                    },
                },
            },
        },
        swapChart: {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [50, 50],
                    backgroundColor: [
                        'rgba(255, 183, 0, 0.7)',
                        'rgba(0, 212, 255, 0.2)',
                    ],
                    borderColor: [
                        'rgba(255, 183, 0, 1)',
                        'rgba(0, 212, 255, 0.5)',
                    ],
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e0e6ff',
                            font: { size: 12, weight: 500 },
                            padding: 15,
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' GB';
                            },
                        },
                    },
                },
            },
        },
        networkUpChart: {
            type: 'line',
            data: {
                labels: Array(120).fill(''),
                datasets: [{
                    label: 'Upload Mbps',
                    data: Array(120).fill(0),
                    borderColor: '#00ff41',
                    backgroundColor: 'rgba(0, 255, 65, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                }],
            },
            options: createChartOptions('Upload', 10),
        },
        networkDownChart: {
            type: 'line',
            data: {
                labels: Array(120).fill(''),
                datasets: [{
                    label: 'Download Mbps',
                    data: Array(120).fill(0),
                    borderColor: '#ff006e',
                    backgroundColor: 'rgba(255, 0, 110, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                }],
            },
            options: createChartOptions('Download', 10),
        },
        diskReadChart: {
            type: 'line',
            data: {
                labels: Array(120).fill(''),
                datasets: [{
                    label: 'Read MB/s',
                    data: Array(120).fill(0),
                    borderColor: '#ffb700',
                    backgroundColor: 'rgba(255, 183, 0, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                }],
            },
            options: createChartOptions('Disk Read', 100),
        },
        diskWriteChart: {
            type: 'line',
            data: {
                labels: Array(120).fill(''),
                datasets: [{
                    label: 'Write MB/s',
                    data: Array(120).fill(0),
                    borderColor: '#ff4db8',
                    backgroundColor: 'rgba(255, 77, 184, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                }],
            },
            options: createChartOptions('Disk Write', 100),
        },
    };

    for (const [id, config] of Object.entries(chartConfigs)) {
        const canvas = document.getElementById(id);
        if (canvas) {
            charts[id] = new Chart(canvas, config);
        }
    }
}

// ─── Update charts ────────────────────────────────────────────────────────────

function padHistory(arr, size = 120) {
    const sliced = arr.slice(-size);
    if (sliced.length >= size) return sliced;
    const fill = sliced.length > 0 ? sliced[0] : 0;
    return Array(size - sliced.length).fill(fill).concat(sliced);
}

function updateCharts(data) {
    // CPU
    if (charts.cpuChart && data.cpu.history) {
        charts.cpuChart.data.datasets[0].data = padHistory(data.cpu.history);
        charts.cpuChart.update('none');
    }

    // Memory
    if (charts.memoryChart) {
        charts.memoryChart.data.datasets[0].data = [
            data.memory.used_gb,
            data.memory.available_gb,
        ];
        charts.memoryChart.options.plugins.title = {
            display: true,
            text: `${formatPercent(data.memory.percent)}`,
        };
        charts.memoryChart.update('none');
    }

    // Swap
    if (charts.swapChart) {
        charts.swapChart.data.datasets[0].data = [
            data.swap.used_gb,
            data.swap.total_gb - data.swap.used_gb,
        ];
        charts.swapChart.update('none');
    }

    // Network
    if (charts.networkUpChart && data.network.up_history) {
        const upMbps = data.network.up_history.map(b => b / (1024 * 1024));
        charts.networkUpChart.data.datasets[0].data = padHistory(upMbps);
        charts.networkUpChart.update('none');
    }

    if (charts.networkDownChart && data.network.down_history) {
        const downMbps = data.network.down_history.map(b => b / (1024 * 1024));
        charts.networkDownChart.data.datasets[0].data = padHistory(downMbps);
        charts.networkDownChart.update('none');
    }

    // Disk
    if (charts.diskReadChart && data.disk.read_history) {
        const readMBps = data.disk.read_history.map(b => b / (1024 * 1024));
        charts.diskReadChart.data.datasets[0].data = padHistory(readMBps);
        charts.diskReadChart.update('none');
    }

    if (charts.diskWriteChart && data.disk.write_history) {
        const writeMBps = data.disk.write_history.map(b => b / (1024 * 1024));
        charts.diskWriteChart.data.datasets[0].data = padHistory(writeMBps);
        charts.diskWriteChart.update('none');
    }
}

// ─── Update metrics ───────────────────────────────────────────────────────────

// ─── Keyboard Shortcuts ───────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts when typing in inputs
    if (document.activeElement.tagName === 'INPUT') return;

    switch (e.key) {
        case '?':
            openModal('helpModal');
            break;
        case 't':
        case 'T':
            toggleTheme();
            break;
        case 's':
        case 'S':
            loadSettings();
            openModal('settingsModal');
            break;
        case 'e':
        case 'E':
            exportMetrics();
            break;
        case 'b':
        case 'B':
            runBenchmark();
            break;
        case 'r':
        case 'R':
            location.reload();
            break;
    }
});

function updateMetrics(data) {
    // Header
    document.getElementById('hostname').textContent = data.system.hostname;
    document.getElementById('os').textContent = data.system.os;
    document.getElementById('uptime').textContent = formatUptime(data.system.uptime_seconds);
    document.getElementById('processes').textContent = data.system.processes;

    // CPU
    document.getElementById('cpuValue').textContent = formatPercent(data.cpu.total);
    document.getElementById('cpuCurrent').textContent = formatPercent(data.cpu.total);
    document.getElementById('cpuBar').style.width = data.cpu.total + '%';
    document.getElementById('cpuFreq').textContent = data.cpu.freq_ghz.toFixed(2) + ' GHz';
    document.getElementById('cpuCores').textContent = data.cpu.per_core.length;

    // Per-core display
    const perCoreGrid = document.getElementById('perCoreGrid');
    if (data.cpu.per_core.length > 0 && perCoreGrid.children.length === 0) {
        data.cpu.per_core.forEach((pct, i) => {
            const item = document.createElement('div');
            item.className = 'core-item';
            item.innerHTML = `
                <span class="core-label">C${i}</span>
                <span class="core-value" data-core="${i}">${formatPercent(pct)}</span>
            `;
            perCoreGrid.appendChild(item);
        });
    } else {
        data.cpu.per_core.forEach((pct, i) => {
            const el = document.querySelector(`[data-core="${i}"]`);
            if (el) el.textContent = formatPercent(pct);
        });
    }

    // Memory
    document.getElementById('memValue').textContent = formatPercent(data.memory.percent);
    document.getElementById('memBar').style.width = data.memory.percent + '%';
    document.getElementById('memTotal').textContent = data.memory.total_gb.toFixed(1) + ' GB';
    document.getElementById('memAvail').textContent = data.memory.available_gb.toFixed(1) + ' GB';

    // Network
    document.getElementById('netUp').textContent = formatMbps(data.network.up_mbps * 1024 * 1024);
    document.getElementById('netDown').textContent = formatMbps(data.network.down_mbps * 1024 * 1024);
    document.getElementById('netUpTotal').textContent = data.network.up_total_gb.toFixed(2) + ' GB';
    document.getElementById('netDownTotal').textContent = data.network.down_total_gb.toFixed(2) + ' GB';

    // Disk
    document.getElementById('diskValue').textContent = formatPercent(data.disk.percent);
    document.getElementById('diskBar').style.width = data.disk.percent + '%';
    document.getElementById('diskTotal').textContent = data.disk.total_gb.toFixed(1) + ' GB';
    document.getElementById('diskRead').textContent = data.disk.read_mbps.toFixed(1) + ' MB/s';
    document.getElementById('diskWrite').textContent = data.disk.write_mbps.toFixed(1) + ' MB/s';

    // Health
    document.getElementById('healthScore').textContent = Math.round(data.health_score);
    document.getElementById('healthLabel').textContent = data.health_score >= 80 ? 'Good' : data.health_score >= 60 ? 'Fair' : 'Poor';

    // Health dial animation
    const dialProgress = document.querySelector('.dial-progress');
    if (dialProgress) {
        const circumference = 2 * Math.PI * 90;
        const offset = circumference - (data.health_score / 100) * circumference;
        dialProgress.style.strokeDasharray = `${circumference - offset}, ${circumference}`;
        dialProgress.style.stroke = getHealthColor(data.health_score);
    }

    // Health badge color
    const badge = document.getElementById('healthBadge');
    badge.style.color = getHealthColor(data.health_score);

    // Check alerts
    checkAlerts(data);
}

// ─── Update processes ─────────────────────────────────────────────────────────

function updateProcesses(procs) {
    const tbody = document.getElementById('processTable');
    tbody.innerHTML = '';

    procs.slice(0, 15).forEach(p => {
        const row = tbody.insertRow();
        const cpu = (p.cpu_percent || 0).toFixed(1);
        const mem = (p.memory_percent || 0).toFixed(2);
        const status = p.status || '?';

        row.innerHTML = `
            <td>${p.pid}</td>
            <td><code>${(p.name || '?').substring(0, 20)}</code></td>
            <td><strong style="color: ${cpu > 50 ? '#ff006e' : '#00d4ff'}">${cpu}%</strong></td>
            <td><strong style="color: ${mem > 5 ? '#ffb700' : '#00ff41'}">${mem}%</strong></td>
            <td><span class="status-badge status-${status === 'running' ? 'running' : 'sleeping'}">${status}</span></td>
        `;
    });
}

// ─── Update interfaces ────────────────────────────────────────────────────────

function updateInterfaces(interfaces) {
    const tbody = document.getElementById('interfaceTable');
    tbody.innerHTML = '';

    interfaces.forEach(iface => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td><code>${iface.name}</code></td>
            <td>${iface.ip}</td>
            <td>${iface.speed}</td>
            <td>
                <span class="status-badge ${iface.is_up ? 'status-up' : 'status-down'}">
                    ${iface.is_up ? '🟢 UP' : '🔴 DOWN'}
                </span>
            </td>
        `;
    });
}

// ─── Update partitions ────────────────────────────────────────────────────────

function updatePartitions(partitions) {
    const tbody = document.getElementById('diskTable');
    tbody.innerHTML = '';

    partitions.forEach(part => {
        const row = tbody.insertRow();
        const pct = part.percent;
        const color = pct >= 85 ? '#ff006e' : pct >= 70 ? '#ffb700' : '#00ff41';

        row.innerHTML = `
            <td><code>${part.mountpoint}</code></td>
            <td>${part.fstype}</td>
            <td>${formatBytes(part.total_gb * 1024**3)}</td>
            <td>${formatBytes(part.used_gb * 1024**3)}</td>
            <td>${formatBytes(part.free_gb * 1024**3)}</td>
            <td>
                <div class="progress-minimal">
                    <div class="progress-minimal-fill" style="width: ${pct}%; background: ${color}"></div>
                </div>
                <span style="color: ${color}; margin-left: 0.5rem;">${formatPercent(pct)}</span>
            </td>
        `;
    });
}

// ─── Update health ────────────────────────────────────────────────────────────

async function updateHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();

        document.getElementById('healthScore').textContent = Math.round(data.score);
        document.getElementById('healthLabel').textContent = data.status;

        const issues = document.getElementById('healthIssues');
        issues.innerHTML = '';
        data.issues.forEach(issue => {
            const li = document.createElement('li');
            li.textContent = issue;
            issues.appendChild(li);
        });
    } catch (e) {
        console.error('Health update failed:', e);
    }
}

// ─── Update clock ─────────────────────────────────────────────────────────────

function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

// ─── Fetch and update all data ────────────────────────────────────────────────

async function fetchAndUpdate() {
    try {
        const [snapshot, procs, ifaces, parts] = await Promise.all([
            fetch('/api/snapshot').then(r => r.json()),
            fetch('/api/processes').then(r => r.json()),
            fetch('/api/network-interfaces').then(r => r.json()),
            fetch('/api/disk-partitions').then(r => r.json()),
        ]);

        updateMetrics(snapshot);
        updateCharts(snapshot);
        updateProcesses(procs);
        updateInterfaces(ifaces);
        updatePartitions(parts);
        updateHealth();
    } catch (e) {
        console.error('Update failed:', e);
    }
}

// ─── Stream updates via EventSource ────────────────────────────────────────────

function streamUpdates() {
    const eventSource = new EventSource('/api/stream');

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            updateMetrics(data);
            updateCharts(data);
        } catch (e) {
            console.error('Stream parse error:', e);
        }
    };

    eventSource.onerror = function() {
        console.error('EventSource error, reconnecting...');
        eventSource.close();
        setTimeout(streamUpdates, 3000);
    };
}

// ─── Initialize ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async function() {
    // Initialize charts first
    initCharts();

    // Fetch initial data
    await fetchAndUpdate();

    // Start real-time updates
    streamUpdates();

    // Periodic updates (every 2 seconds for processes/interfaces/partitions)
    setInterval(async () => {
        try {
            const [procs, ifaces, parts] = await Promise.all([
                fetch('/api/processes').then(r => r.json()),
                fetch('/api/network-interfaces').then(r => r.json()),
                fetch('/api/disk-partitions').then(r => r.json()),
            ]);
            updateProcesses(procs);
            updateInterfaces(ifaces);
            updatePartitions(parts);
        } catch (e) {
            console.error('Periodic update failed:', e);
        }
    }, 2000);

    // Clock update
    updateClock();
    setInterval(updateClock, 1000);

    // Health check every 5 seconds
    setInterval(updateHealth, 5000);
});
