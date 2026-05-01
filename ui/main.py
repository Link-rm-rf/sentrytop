import os
import sys
import time
import threading
from blessed import Terminal
from components.database import Database
from components.fifo_reader import FifoReader
from components.stats_cache import StatsCache
from modes.monitor import MonitorMode
from modes.process_manager import ProcessManagerMode
from modes.network_insight import NetworkInsightMode
from modes.log_viewer import LogViewerMode

class SentryTopApp:
    def __init__(self):
        self.term = Terminal()
        # Fallback for testing if /opt/sentrytop is not writable
        db_path = "/opt/sentrytop/alerts.db"
        fifo_path = "/opt/sentrytop/alerts.fifo"
        
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.access(os.path.dirname(db_path), os.W_OK):
            db_path = os.path.join(root, "alerts.db")
            fifo_path = os.path.join(root, "alerts.fifo")
            
        self.db = Database(db_path)
        self.fifo_reader = FifoReader(self.db, fifo_path)
        self.stats_cache = StatsCache()
        
        self.modes = {
            'F1': MonitorMode(self),
            'F2': ProcessManagerMode(self),
            'F3': NetworkInsightMode(self),
            'F4': LogViewerMode(self)
        }
        self.current_mode_key = 'F1'
        self.running = True

    def run(self):
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            # Clear screen once
            print(self.term.home + self.term.black_on_black + self.term.clear)
            
            while self.running:
                # Handle input
                key = self.term.inkey(timeout=0.066) # ~15 FPS
                if key:
                    self._handle_input(key)

                # Render
                self._render()

    def _handle_input(self, key):
        if key.name == 'KEY_F1': self.current_mode_key = 'F1'
        elif key.name == 'KEY_F2': self.current_mode_key = 'F2'
        elif key.name == 'KEY_F3': self.current_mode_key = 'F3'
        elif key.name == 'KEY_F4': self.current_mode_key = 'F4'
        elif key.lower() == 'q': self.running = False
        else:
            self.modes[self.current_mode_key].handle_input(key)

    def _render(self):
        mode = self.modes[self.current_mode_key]
        mode.render()
        self._render_footer()

    def _render_footer(self):
        stats = self.stats_cache.get_stats()
        footer = self.term.move_y(self.term.height - 1)
        footer += self.term.green_on_black + " [F1] Monitor [F2] ProcMgr [F3] Network [F4] Logs [Q] Quit "
        footer += self.term.move_x(self.term.width - 30)
        footer += f"CPU: {stats['cpu']}% | MEM: {stats['memory']}% "
        print(footer, end='', flush=True)

if __name__ == "__main__":
    app = SentryTopApp()
    app.run()
