import os
import json
import threading
import time

class FifoReader:
    def __init__(self, db, fifo_path="/opt/sentrytop/alerts.fifo"):
        self.db = db
        self.fifo_path = fifo_path
        self.running = True
        self.new_alerts = []
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        # Create FIFO if it doesn't exist (fallback)
        if not os.path.exists(self.fifo_path):
            try:
                os.mkfifo(self.fifo_path)
                os.chmod(self.fifo_path, 0o666)
            except Exception:
                pass

        while self.running:
            try:
                # Opening FIFO blocks until there's a writer
                with open(self.fifo_path, 'r') as fifo:
                    for line in fifo:
                        if not self.running: break
                        try:
                            alert = json.loads(line)
                            self.db.insert_alert(alert)
                            with self.lock:
                                self.new_alerts.append(alert)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                time.sleep(1)

    def get_new_alerts(self):
        with self.lock:
            alerts = list(self.new_alerts)
            self.new_alerts.clear()
            return alerts

    def stop(self):
        self.running = False
