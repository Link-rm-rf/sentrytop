#!/usr/bin/env python3
"""
SentryTop CLI - Retro-styled EDR Monitoring Interface.
Version: 1.1.0
Author: SentryTop Lead Security Engineer
"""

import os
import sys
import time
import subprocess
import threading
import psutil
import select
import tty
import termios
import random
import re
import logging
from collections import deque
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# Third-party imports
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich import box
    from rich.errors import ConsoleError
except ImportError:
    print("Error: Missing dependency. Please run: pip install rich psutil")
    sys.exit(1)

# Configuration
CONFIG: Dict[str, Any] = {
    "colors": {"primary": "#00FF00", "accent": "#00FFFF", "warning": "#FF0000", "background": "#000000"},
    "ui": {
        "refresh_rate": 10,
        "log_limit": 100,
        "visible_lines": 22,
        "glitch_steps": 12,
        "glitch_delay": 0.04,
        "banner": r"""
███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ 
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗
███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝     ██║   ██║   ██║██╔═══╝ 
███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║      ██║   ╚██████╔╝██║     
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝
""",
        "version": "v1.1.0"
    },
    "threat_keywords": ["[CRIT]", "[WARN]", "[BEAC]", "Unusual Port"],
    "safe_keywords": ["New safe connection"]
}

# Absolute path resolution
def get_project_root() -> str:
    """Dynamically resolves the project root based on script location or environment."""
    # First, try to use the location of this script
    script_path = os.path.abspath(__file__)
    # If we are in ui/sentrytop_cli.py, root is two levels up
    root = os.path.dirname(os.path.dirname(script_path))
    
    if os.path.exists(os.path.join(root, "scripts", "sentrytop")):
        return root
        
    # Fallback to /opt if it exists and looks like ours
    if os.path.exists("/opt/sentrytop/scripts/sentrytop"):
        return "/opt/sentrytop"
        
    return root

def get_log_path() -> str:
    root = get_project_root()
    return os.path.join(root, "sentrytop_cli.log")

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@dataclass
class CLIState:
    logs: deque = field(default_factory=lambda: deque(maxlen=CONFIG["ui"]["log_limit"]))
    threat_count: int = 0
    safe_count: int = 0
    paused: bool = False
    verbose: bool = True
    running: bool = True
    start_time: float = field(default_factory=time.time)
    log_lock: threading.Lock = field(default_factory=threading.Lock)
    footer_progress: Progress = field(default=None)

class SentryTopUI:
    def __init__(self, console: Console, state: CLIState) -> None:
        self.console = console
        self.state = state
        self.layout = self._create_layout()
        self.state.footer_progress = Progress(
            TextColumn("[progress.description]{task.description}"), 
            BarColumn(bar_width=30, complete_style=CONFIG["colors"]["accent"]), 
            console=self.console
        )
        self.state.footer_progress.add_task("Core Heartbeat", total=100)

    def _create_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(Layout(name="header", size=10), Layout(name="status", size=3), Layout(name="main"), Layout(name="footer", size=3))
        return layout

    def render_tick(self) -> Layout:
        self._render_header()
        self._render_status()
        self._render_main()
        self._render_footer()
        return self.layout

    def _render_header(self) -> None:
        header_text = Text(CONFIG["ui"]["banner"], style=CONFIG["colors"]["primary"], justify="center")
        header_text.append(f"\nSentryTop {CONFIG['ui']['version']} | EDR Monitoring System", style=CONFIG["colors"]["accent"])
        self.layout["header"].update(Panel(header_text, border_style=CONFIG["colors"]["primary"], box=box.SQUARE))

    def _render_status(self) -> None:
        status_table = Table.grid(expand=True)
        status_table.add_column(justify="left", ratio=1)
        status_table.add_column(justify="right", ratio=1)
        status_msg = Text(" EDR Agent Running", style=f"bold {CONFIG['colors']['primary']}")
        if self.state.paused: status_msg.append(" [PAUSED]", style="bold yellow")
        counters = Text()
        counters.append("THREATS: ", style=CONFIG["colors"]["accent"])
        counters.append(str(self.state.threat_count), style=f"bold {CONFIG['colors']['warning']}")
        counters.append(" | ", style=CONFIG["colors"]["primary"])
        counters.append("SAFE: ", style=CONFIG["colors"]["accent"])
        counters.append(str(self.state.safe_count), style=f"bold {CONFIG['colors']['primary']}")
        status_table.add_row(status_msg, counters)
        self.layout["status"].update(Panel(status_table, border_style=CONFIG["colors"]["primary"], title="[STATUS]", title_align="left", box=box.SQUARE))

    def _render_main(self) -> None:
        log_panel_text = Text()
        with self.state.log_lock:
            visible_logs = list(self.state.logs)[-CONFIG["ui"]["visible_lines"]:]
        for line in visible_logs:
            log_panel_text.append(line)
            log_panel_text.append("\n")
        self.layout["main"].update(Panel(log_panel_text, border_style=CONFIG["colors"]["primary"], title="[REAL-TIME MONITOR]", title_align="left", box=box.SQUARE))

    def _render_footer(self) -> None:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        footer_grid = Table.grid(expand=True)
        footer_grid.add_column(justify="left", ratio=1)
        footer_grid.add_column(justify="right", ratio=1)
        uptime = int(time.time() - self.state.start_time)
        metrics = Text(f"Uptime: {uptime}s | SYS CPU: {cpu}% | SYS MEM: {mem}%", style=CONFIG["colors"]["accent"])
        
        # Update existing progress task instead of recreating
        task_id = self.state.footer_progress.task_ids[0]
        self.state.footer_progress.update(task_id, completed=(time.time() * 25) % 100)
        
        footer_grid.add_row(metrics, self.state.footer_progress)
        self.layout["footer"].update(Panel(footer_grid, border_style=CONFIG["colors"]["primary"], box=box.SQUARE))

class DataPipeline:
    def __init__(self, state: CLIState, mock: bool = False) -> None:
        self.state = state
        self.mock = mock
        self.process: Optional[subprocess.Popen] = None
        self.ansi_strip = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def initialize(self) -> None:
        if self.mock:
            threading.Thread(target=self._mock_generator, daemon=True).start()
            return
        
        root = get_project_root()
        engine_path = os.path.join(root, "scripts", "sentrytop")
        
        if not os.path.exists(engine_path):
            raise RuntimeError(f"Engine script not found at {engine_path}")

        try:
            self.process = subprocess.Popen(
                [engine_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, cwd=root, env=os.environ.copy(), errors='replace'
            )
            threading.Thread(target=self._pipe_reader, args=(self.process.stdout, "stdout"), daemon=True).start()
            threading.Thread(target=self._pipe_reader, args=(self.process.stderr, "stderr"), daemon=True).start()
        except Exception as e:
            raise RuntimeError(f"Pipeline failure: {e}")

    def _pipe_reader(self, pipe: Any, stream_name: str) -> None:
        try:
            for line in iter(pipe.readline, ''):
                if not self.state.running: break
                if line: self._process_payload(line)
        except Exception: pass

    def _process_payload(self, line: str) -> None:
        clean_text = self.ansi_strip.sub('', line).strip()
        if not clean_text: return
        styled = Text(clean_text)
        if any(tag in clean_text for tag in CONFIG["threat_keywords"]):
            self.state.threat_count += 1
            styled.stylize(f"bold {CONFIG['colors']['warning']}")
        elif any(tag in clean_text for tag in CONFIG["safe_keywords"]):
            self.state.safe_count += 1
            styled.stylize(CONFIG["colors"]["accent"])
        else:
            styled.stylize(CONFIG["colors"]["primary"])

        if not self.state.paused:
            with self.state.log_lock:
                self.state.logs.append(styled)

    def _mock_generator(self) -> None:
        samples = ["New safe connection: 1.1.1.1", "[WARN] Unusual Port Connection!"]
        while self.state.running:
            time.sleep(random.uniform(0.1, 1.0))
            self._process_payload(random.choice(samples))

    def terminate(self) -> None:
        if self.process:
            self.process.terminate()

class InputController:
    def __init__(self, state: CLIState) -> None:
        self.state = state

    def run_loop(self) -> None:
        try:
            orig_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            while self.state.running:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key == 'q': self.state.running = False
                    elif key == 'p': self.state.paused = not self.state.paused
                    elif key == 'v': self.state.verbose = not self.state.verbose
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
        except Exception: pass

def main() -> None:
    state = CLIState()
    console = Console()
    mock_active = "--mock" in sys.argv
    
    if not mock_active and os.getuid() != 0 and os.environ.get("NOSUDO") != "1":
        console.print("[bold red]Error: SentryTop requires root privileges.[/bold red]")
        return

    ui = SentryTopUI(console, state)
    pipeline = DataPipeline(state, mock=mock_active)
    
    try:
        pipeline.initialize()
    except Exception as e:
        console.print(f"[bold red]FATAL: {e}[/bold red]")
        return

    threading.Thread(target=InputController(state).run_loop, daemon=True).start()

    try:
        with Live(ui.layout, refresh_per_second=CONFIG["ui"]["refresh_rate"], screen=True) as live:
            while state.running:
                if not mock_active and pipeline.process and pipeline.process.poll() is not None:
                    break
                live.update(ui.render_tick())
                time.sleep(1.0 / CONFIG["ui"]["refresh_rate"])
    except Exception: pass
    finally:
        state.running = False
        pipeline.terminate()
        console.clear()
        print("SentryTop CLI: Operational shutdown complete.")

if __name__ == "__main__":
    main()
