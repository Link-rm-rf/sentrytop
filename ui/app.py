import time
import os
from .rendering.engine import RenderEngine
from .components.keyboard import KeyboardHandler
from .components.alerts import AlertQueue
from .components.database import Database
from .components.fifo_reader import FifoReader
from .components.stats_cache import StatsCache
from .utils.logger import logger
from .utils.constants import (
    REFRESH_RATE, MODE_MONITOR, MODE_PROCESS, MODE_NETWORK, MODE_LOGS, MODE_MENU,
    DEFAULT_DB_PATH, DEFAULT_FIFO_PATH, PROJECT_ROOT
)
from .modes.monitor import MonitorMode
from .modes.process_manager import ProcessManagerMode
from .modes.network_insight import NetworkInsightMode
from .modes.log_viewer import LogViewerMode
from .modes.main_menu import MainMenuMode

class SentryTopApp:
    def __init__(self):
        self.renderer = RenderEngine()
        self.keyboard = KeyboardHandler(self.renderer.term)
        self.alert_queue = AlertQueue()
        
        # Path resolution
        db_path = DEFAULT_DB_PATH
        fifo_path = DEFAULT_FIFO_PATH
        if not os.access(os.path.dirname(db_path), os.W_OK):
            db_path = os.path.join(PROJECT_ROOT, "alerts.db")
            fifo_path = os.path.join(PROJECT_ROOT, "alerts.fifo")
            
        self.db = Database(db_path)
        self.fifo_reader = FifoReader(self.db, self.alert_queue, fifo_path) 
        self.stats_cache = StatsCache()
        
        self.modes = {
            MODE_MENU: MainMenuMode(self),
            MODE_MONITOR: MonitorMode(self),
            MODE_PROCESS: ProcessManagerMode(self),
            MODE_NETWORK: NetworkInsightMode(self),
            MODE_LOGS: LogViewerMode(self)
        }
        self.current_mode_key = MODE_MENU
        self.running = True

    def run(self):
        logger.info("Starting SentryTop App")
        self.keyboard.start()
        
        with self.renderer.term.fullscreen(), self.renderer.term.cbreak(), self.renderer.term.hidden_cursor():
            self.renderer.clear()
            
            try:
                while self.running:
                    start_time = time.time()
                    
                    # 1. Handle all pending input
                    while True:
                        key = self.keyboard.get_key()
                        if not key:
                            break
                        try:
                            self._handle_input(key)
                        except Exception as e:
                            logger.error(f"Input error: {e}")

                    # 2. Update state
                    try:
                        self.modes[self.current_mode_key].update()
                    except Exception as e:
                        logger.error(f"Mode update error: {e}")

                    # 3. Render
                    if self.renderer.term.width < 80 or self.renderer.term.height < 24:
                        self.renderer.begin_frame()
                        print(self.renderer.move_to(0, 0) + self.renderer.get_color("bright_green")("Terminal too small. Minimum size: 80x24"), end='', flush=False)
                        self.renderer.end_frame()
                    else:
                        self.renderer.begin_frame()
                        try:
                            self._render()
                        except Exception as e:
                            logger.error(f"Render error: {e}")
                        self.renderer.end_frame()
                    
                    # 4. Cap FPS (15 FPS target)
                    elapsed = time.time() - start_time
                    wait = max(0, (1.0 / REFRESH_RATE) - elapsed)
                    if wait > 0:
                        time.sleep(wait)
            except Exception as e:
                logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            finally:
                self.cleanup()

    def _handle_input(self, key):
        # Allow checking string values safely
        k_name = key.name if hasattr(key, 'name') else None
        
        if key == '1' or k_name == 'KEY_F1':
            self.current_mode_key = MODE_MONITOR
            self.modes[self.current_mode_key].on_enter()
        elif key == '2' or k_name == 'KEY_F2':
            self.current_mode_key = MODE_PROCESS
            self.modes[self.current_mode_key].on_enter()
        elif key == '3' or k_name == 'KEY_F3':
            self.current_mode_key = MODE_NETWORK
            self.modes[self.current_mode_key].on_enter()
        elif key == '4' or k_name == 'KEY_F4':
            self.current_mode_key = MODE_LOGS
            self.modes[self.current_mode_key].on_enter()
        elif str(key).lower() == 'q':
            self.running = False
        else:
            self.modes[self.current_mode_key].handle_input(key)

    def _render(self):
        mode = self.modes[self.current_mode_key]
        mode.render()
        if self.current_mode_key != MODE_MENU:
            self._render_footer()

    def render_progress_bar(self, value, width=12):
        filled = int((value / 100) * width)
        # Using blocks and spaces for empty
        bar = "█" * filled + " " * (width - filled)
        return bar

    def _render_footer(self):
        stats = self.stats_cache.get_stats()
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = f"{uptime_seconds // 3600:02d}:{(uptime_seconds % 3600) // 60:02d}:{uptime_seconds % 60:02d}"
        
        cpu = stats.get('cpu', 0.0)
        mem = stats.get('memory', 0.0)
        cpu_bar = self.render_progress_bar(cpu, width=15)
        mem_bar = self.render_progress_bar(mem, width=15)
        
        threat_count = self.alert_queue.threat_count
        total_alerts = self.alert_queue.size
        
        # New requested footer exact format
        cpu_text = f"CPU: {cpu:.1f}% "
        mem_text = f"MEM: {mem:.1f}% "
        
        y = self.renderer.term.height - 1
        
        # We want to space them out evenly
        status_parts = [
            f"CPU: {cpu:.1f}% {cpu_bar}",
            f"MEM: {mem:.1f}% {mem_bar}",
            f"UPTIME: {uptime_str}",
            f"ALERTS: {total_alerts}"
        ]
        
        spacing = (self.renderer.term.width - sum(len(p) for p in status_parts) - 15) // 3
        if spacing < 2: spacing = 2
        
        space_str = " " * spacing
        
        # We manually colorize the critical part
        crit_part = f" ({threat_count} CRITICAL)"
        
        # Print with colors
        print(self.renderer.term.move_xy(0, y), end='', flush=False)
        
        # Background
        print(self.renderer.term.on_black, end='', flush=False)
        
        print(self.renderer.term.green(status_parts[0] + space_str + status_parts[1] + space_str + status_parts[2] + space_str + status_parts[3]), end='', flush=False)
        print(self.renderer.term.red(crit_part), end='', flush=False)

    def cleanup(self):
        logger.info("Shutting down SentryTop App")
        self.keyboard.stop()
        self.running = False
