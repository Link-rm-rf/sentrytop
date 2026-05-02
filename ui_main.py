#!/usr/bin/env python3
"""
SentryTop v1.1.0 - Retro CRT TUI Entry Point
A high-fidelity terminal interface matching the v1.1.0 ADVANCED SYSTEM THREAT MONITOR aesthetic.
"""

import os
import sys
import time
import tty
import termios
import select
from datetime import datetime

# Libraries
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.table import Table
from rich import box

# SentryTop Components (Relative imports since we are in project root)
from ui.components.stats_cache import StatsCache
from ui.components.alerts import AlertQueue
from ui.components.database import Database
from ui.components.fifo_reader import FifoReader
from ui.utils.constants import (
    VERSION, DEFAULT_DB_PATH, DEFAULT_FIFO_PATH, PROJECT_ROOT
)
from ui.utils.logger import logger

class RawInput:
    """Handles raw terminal input without external dependencies like blessed."""
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = None

    def __enter__(self):
        try:
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        except Exception:
            pass
        return self

    def __exit__(self, type, value, traceback):
        if self.old_settings:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self):
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

class SentryTopTUI:
    def __init__(self):
        self.console = Console(force_terminal=True, color_system="truecolor")
        self.stats_cache = StatsCache()
        self.alert_queue = AlertQueue()
        self.start_time = time.time()
        
        # Database and FIFO Setup
        db_path = DEFAULT_DB_PATH
        fifo_path = DEFAULT_FIFO_PATH
        if not os.access(os.path.dirname(db_path), os.W_OK):
            db_path = os.path.join(PROJECT_ROOT, "alerts.db")
            fifo_path = os.path.join(PROJECT_ROOT, "alerts.fifo")
            
        self.db = Database(db_path)
        self.fifo_reader = FifoReader(self.db, self.alert_queue, fifo_path)
        
        self.running = True
        
        # CRT Aesthetic Constants
        self.PRIMARY_GREEN = "#00FF41" 
        self.BG_BLACK = "#000000"
        self.CRITICAL_RED = "#FF0000"

    def get_ascii_logo(self):
        logo = """
 ███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ 
 ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗
 ███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝
 ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝     ██║   ██║   ██║██╔═══╝ 
 ███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║      ██║   ╚██████╔╝██║     
 ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝     
        """
        return Text(logo, style=f"bold {self.PRIMARY_GREEN}")

    def make_header(self) -> Panel:
        logo = self.get_ascii_logo()
        tagline = Text(f"{VERSION} - ADVANCED SYSTEM THREAT MONITOR", style=f"bold {self.PRIMARY_GREEN}")
        
        # Combine logo and tagline into a single layout-friendly object
        content = Table.grid()
        content.add_column(justify="center")
        content.add_row(logo)
        content.add_row(tagline)
        
        return Panel(
            Align.center(content),
            style=f"{self.PRIMARY_GREEN} on {self.BG_BLACK}",
            box=box.DOUBLE_EDGE,
            padding=(1, 1)
        )

    def make_menu(self) -> Panel:
        menu_items = [
            "[1] MONITOR (LIVE THREAT FEED)",
            "[2] PROCESS MANAGER",
            "[3] NETWORK INSIGHT",
            "[4] ALERT LOGS",
            "[Q] QUIT SENTRYTOP"
        ]
        
        table = Table.grid(padding=(1, 2))
        table.add_column(justify="center", min_width=40)
        
        for item in menu_items:
            table.add_row(Text(item, style=f"bold {self.PRIMARY_GREEN}"))
            
        return Panel(
            Align.center(table, vertical="middle"),
            title="[ SYSTEM COMMAND MENU ]",
            style=f"{self.PRIMARY_GREEN} on {self.BG_BLACK}",
            box=box.HEAVY_EDGE
        )

    def make_footer(self) -> Panel:
        stats = self.stats_cache.get_stats()
        cpu_val = stats.get('cpu', 0.0)
        mem_val = stats.get('memory', 0.0)
        
        uptime_sec = int(time.time() - self.start_time)
        uptime_str = f"{uptime_sec // 3600:02d}:{(uptime_sec % 3600) // 60:02d}:{uptime_sec % 60:02d}"
        
        alerts_total = self.alert_queue.size
        alerts_crit = self.alert_queue.threat_count
        
        def get_bar(val):
            filled = int(val / 10)
            return f"[{'|' * filled}{'.' * (10 - filled)}] {val:>4.1f}%"

        footer_table = Table.grid(expand=True)
        footer_table.add_column(ratio=1)
        footer_table.add_column(ratio=1)
        footer_table.add_column(ratio=1)
        footer_table.add_column(ratio=1)
        
        alerts_text = Text(f"ALERTS: {alerts_total} ", style=self.PRIMARY_GREEN)
        if alerts_crit > 0:
            alerts_text.append(f"({alerts_crit} CRITICAL)", style=f"bold {self.CRITICAL_RED}")
        else:
            alerts_text.append("(0 CRITICAL)", style=self.PRIMARY_GREEN)

        footer_table.add_row(
            Text(f"CPU: {get_bar(cpu_val)}", style=self.PRIMARY_GREEN),
            Text(f"MEM: {get_bar(mem_val)}", style=self.PRIMARY_GREEN),
            Text(f"UPTIME: {uptime_str}", style=self.PRIMARY_GREEN),
            alerts_text
        )
        
        return Panel(
            footer_table,
            style=f"{self.PRIMARY_GREEN} on {self.BG_BLACK}",
            box=box.HORIZONTALS,
            padding=(0, 1)
        )

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(self.make_header(), name="header", size=12),
            Layout(self.make_menu(), name="body"),
            Layout(self.make_footer(), name="footer", size=3)
        )
        return layout

    def run(self):
        with RawInput() as input_handler:
            with Live(self.generate_layout(), console=self.console, screen=True, refresh_per_second=4) as live:
                while self.running:
                    # Update the layout
                    live.update(self.generate_layout())
                    
                    # Handle Input
                    key = input_handler.get_key()
                    if key:
                        self._handle_input(key)
                        
                    time.sleep(0.05)

    def _handle_input(self, key):
        k = str(key).lower()
        if k == 'q':
            self.running = False
        # Navigation handled by numerical keys

    def cleanup(self):
        self.stats_cache.stop()
        self.fifo_reader.stop()

if __name__ == "__main__":
    tui = SentryTopTUI()
    try:
        tui.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"TUI Fatal Error: {e}", exc_info=True)
    finally:
        tui.cleanup()
