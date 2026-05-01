import sqlite3
import threading
import os

class Database:
    def __init__(self, db_path="/opt/sentrytop/alerts.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    type TEXT,
                    pid INTEGER,
                    process TEXT,
                    source_ip TEXT,
                    port INTEGER,
                    threat_level TEXT,
                    info TEXT
                )
            ''')
            conn.commit()
            conn.close()

    def insert_alert(self, alert_data):
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute('''
                    INSERT INTO alerts (timestamp, type, pid, process, source_ip, port, threat_level, info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_data.get('timestamp'),
                    alert_data.get('type'),
                    alert_data.get('pid'),
                    alert_data.get('process'),
                    alert_data.get('source_ip'),
                    alert_data.get('port'),
                    alert_data.get('threat'),
                    alert_data.get('info')
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"DB Error: {e}")

    def get_alerts(self, limit=100):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows

    def get_alerts_for_pid(self, pid):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('SELECT threat_level, info FROM alerts WHERE pid = ?', (pid,))
            rows = cursor.fetchall()
            conn.close()
            return rows
