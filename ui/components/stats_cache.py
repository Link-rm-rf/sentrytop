import psutil
import threading
import time

class StatsCache:
    def __init__(self):
        self.processes = []
        self.connections = []
        self.cpu = 0
        self.memory = 0
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        while self.running:
            try:
                # Update processes
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'ppid', 'exe', 'status']):
                    try:
                        info = p.info
                        if info.get('exe') is None:
                            info['exe'] = "ACCESS DENIED"
                        procs.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Update connections
                conns = []
                try:
                    # Filter for ESTABLISHED and LISTEN
                    for c in psutil.net_connections(kind='inet'):
                        conns.append(c)
                except (psutil.AccessDenied):
                    pass

                with self.lock:
                    self.processes = sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)
                    self.connections = conns
                    self.cpu = psutil.cpu_percent(interval=None)
                    self.memory = psutil.virtual_memory().percent

            except Exception as e:
                from ..utils.logger import logger
                logger.error(f"StatsCache update loop error: {e}")
            
            time.sleep(1) # Refresh every 1 second per requirements

    def get_stats(self):
        with self.lock:
            return {
                'processes': self.processes,
                'connections': self.connections,
                'cpu': self.cpu,
                'memory': self.memory
            }

    def stop(self):
        self.running = False
