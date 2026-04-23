"""
Database models and utilities for historical metrics storage.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading

DB_PATH = Path(__file__).parent / 'metrics.db'

class MetricsDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_db()

    def init_db(self):
        """Initialize database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_gb REAL,
                    memory_total_gb REAL,
                    swap_percent REAL,
                    network_up_mbps REAL,
                    network_down_mbps REAL,
                    disk_percent REAL,
                    disk_read_mbps REAL,
                    disk_write_mbps REAL,
                    health_score REAL,
                    raw_data TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)')
            conn.commit()

    def store_metrics(self, snapshot):
        """Store a snapshot of metrics."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO metrics (
                        cpu_percent, memory_percent, memory_used_gb, memory_total_gb,
                        swap_percent, network_up_mbps, network_down_mbps,
                        disk_percent, disk_read_mbps, disk_write_mbps,
                        health_score, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot['cpu']['total'],
                    snapshot['memory']['percent'],
                    snapshot['memory']['used_gb'],
                    snapshot['memory']['total_gb'],
                    snapshot['swap']['percent'],
                    snapshot['network']['up_mbps'],
                    snapshot['network']['down_mbps'],
                    snapshot['disk']['percent'],
                    snapshot['disk']['read_mbps'],
                    snapshot['disk']['write_mbps'],
                    snapshot['health_score'],
                    json.dumps(snapshot),
                ))
                conn.commit()

    def get_metrics(self, hours=24):
        """Get metrics from last N hours."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = datetime.now() - timedelta(hours=hours)
                rows = conn.execute(
                    'SELECT * FROM metrics WHERE timestamp > ? ORDER BY timestamp',
                    (cutoff.isoformat(),)
                ).fetchall()
                return [dict(row) for row in rows]

    def get_stats(self, hours=24):
        """Get aggregated statistics for time period."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = datetime.now() - timedelta(hours=hours)
                stats = conn.execute('''
                    SELECT
                        AVG(cpu_percent) as avg_cpu,
                        MAX(cpu_percent) as max_cpu,
                        AVG(memory_percent) as avg_memory,
                        MAX(memory_percent) as max_memory,
                        AVG(health_score) as avg_health,
                        COUNT(*) as samples
                    FROM metrics
                    WHERE timestamp > ?
                ''', (cutoff.isoformat(),)).fetchone()
                return dict(stats) if stats else {}

    def cleanup_old(self, days=30):
        """Delete metrics older than N days."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = datetime.now() - timedelta(days=days)
                conn.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff.isoformat(),))
                conn.commit()
