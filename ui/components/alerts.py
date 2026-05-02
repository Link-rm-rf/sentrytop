import threading
from collections import deque
from ..utils.constants import LOG_LIMIT

class AlertQueue:
    def __init__(self, maxlen=LOG_LIMIT):
        self._queue = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self.threat_count = 0
        self.safe_count = 0

    def add(self, alert_data: dict):
        with self._lock:
            self._queue.append(alert_data)
            severity = alert_data.get('severity', '').upper()
            if severity in ['CRITICAL', 'WARN', 'HIGH']:
                self.threat_count += 1
            elif severity == 'SAFE':
                self.safe_count += 1

    def get_all(self):
        with self._lock:
            return list(self._queue)

    def clear(self):
        with self._lock:
            self._queue.clear()
            self.threat_count = 0
            self.safe_count = 0

    @property
    def size(self):
        with self._lock:
            return len(self._queue)
