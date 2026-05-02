import os
import json
import threading
import time

class FifoReader:
    def __init__(self, db, alert_queue, fifo_path="/opt/sentrytop/alerts.fifo"):
        self.db = db
        self.alert_queue = alert_queue
        self.fifo_path = fifo_path
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        from ..utils.logger import logger
        # Create FIFO if it doesn't exist (fallback)
        if not os.path.exists(self.fifo_path):
            try:
                os.mkfifo(self.fifo_path)
                os.chmod(self.fifo_path, 0o666)
            except Exception as e:
                logger.error(f"Failed to create FIFO at {self.fifo_path}: {e}")

        while self.running:
            try:
                # Opening FIFO blocks until there's a writer
                with open(self.fifo_path, 'r') as fifo:
                    for line in fifo:
                        if not self.running: break
                        try:
                            alert = json.loads(line)
                            self.db.insert_alert(alert)
                            self.alert_queue.add(alert)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"FIFO read error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
