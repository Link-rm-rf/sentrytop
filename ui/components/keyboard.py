import queue
import threading
from blessed import Terminal

class KeyboardHandler:
    def __init__(self, term: Terminal):
        self.term = term
        self.event_queue = queue.Queue()
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._input_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _input_loop(self):
        while self.running:
            # Short timeout to allow checking self.running
            key = self.term.inkey(timeout=0.1)
            if key:
                self.event_queue.put(key)

    def get_key(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None
