#!/usr/bin/env python3
"""
SentryTop CLI - Retro-styled EDR Monitoring Interface.
Version: 1.1.0
Author: SentryTop Lead Security Engineer

What: A high-performance terminal user interface (TUI) for the SentryTop EDR agent.
Why: Security analysts require a fast, distraction-free, and real-time visualization of endpoint threats and network connections directly within a terminal environment.
How: Utilizes the 'rich' library for dynamic console rendering, 'psutil' for local system telemetry, and a multi-threaded producer-consumer architecture to asynchronously parse logs from the Java correlator without blocking the main rendering loop.
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

# Third-party imports with verification
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

# Global Configuration Dictionary - No hardcoded values in logic
CONFIG: Dict[str, Any] = {
    "colors": {
        "primary": "#00FF00",   # Bright Green (CRT Style)
        "accent": "#00FFFF",    # Cyan (Metrics/Info)
        "warning": "#FF0000",   # Red (Threats)
        "background": "#000000" # Pure Black
    },
    "ui": {
        "refresh_rate": 10,     # Updates per second
        "log_limit": 100,       # Max log lines in memory
        "visible_lines": 22,    # Number of lines to display in the main panel
        "glitch_steps": 12,     # Startup animation frames
        "glitch_delay": 0.04,   # Delay between glitch frames
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
    "paths": {
        "engine_script": "../scripts/sentrytop",
        "log_file": "sentrytop_cli.log"
    },
    "mock": {
        "threat_rate": 0.15,
        "latency_min": 0.05,
        "latency_max": 0.8,
        "threat_samples": [
            "[CRIT] BEACON DETECTED: Unknown Remote Endpoint 45.33.32.156:443",
            "[WARN] SUSPICIOUS PROCESS: /tmp/.hidden_shell (Parent: nginx)",
            "[BEAC] EXFILTRATION ATTEMPT: 1.2 GB to region: RU"
        ],
        "safe_samples": [
            "New safe connection: 192.168.1.10:53 (DNS)",
            "New safe connection: 172.16.0.4:443 (HTTPS)",
            "New safe connection: 10.0.0.5:22 (SSH)"
        ]
    },
    "threat_keywords": ["[CRIT]", "[WARN]", "[BEAC]"],
    "safe_keywords": ["New safe connection"]
}

# Logger setup for background audit
logging.basicConfig(
    filename=CONFIG["paths"]["log_file"],
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class CLIState:
    """
    Maintains the thread-safe global state of the CLI application.
    
    What: A centralized data store for metrics and logs.
    Why: Prevents race conditions between the input thread, parsing threads, and the rendering main thread.
    How: Uses threading.Lock for complex mutations and collections.deque for O(1) thread-safe log rotations.
    """
    logs: deque = field(default_factory=lambda: deque(maxlen=CONFIG["ui"]["log_limit"]))
    threat_count: int = 0
    safe_count: int = 0
    paused: bool = False
    verbose: bool = True
    running: bool = True
    start_time: float = field(default_factory=time.time)
    log_lock: threading.Lock = field(default_factory=threading.Lock)

class SentryTopUI:
    """
    Orchestrates the UI composition and layout updates.
    
    What: Handles all Rich library layout declarations and updates.
    Why: Separates the visual representation logic from data fetching and state management.
    How: Exposes a `render_tick` method called by the `Live` context manager every refresh cycle.
    """
    def __init__(self, console: Console, state: CLIState) -> None:
        """
        Initializes the UI with a console instance and global state.
        """
        self.console = console
        self.state = state
        self.layout = self._create_layout()

    def _create_layout(self) -> Layout:
        """
        Initializes the master layout structure.
        
        Returns:
            Layout: The root Rich Layout object with split panes.
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=10),
            Layout(name="status", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        return layout

    def render_tick(self) -> Layout:
        """
        Refreshes all sub-components of the layout.
        
        Returns:
            Layout: The updated layout ready for rendering.
        """
        try:
            self._render_header()
            self._render_status()
            self._render_main()
            self._render_footer()
        except Exception as e:
            logger.error(f"Render tick failed: {e}")
        return self.layout

    def _render_header(self) -> None:
        """Renders the top ASCII art banner."""
        header_text = Text(CONFIG["ui"]["banner"], style=CONFIG["colors"]["primary"], justify="center")
        header_text.append(f"\nSentryTop {CONFIG['ui']['version']} | EDR Monitoring System", style=CONFIG["colors"]["accent"])
        self.layout["header"].update(Panel(header_text, border_style=CONFIG["colors"]["primary"], box=box.SQUARE))

    def _render_status(self) -> None:
        """Renders the status bar indicating operational state and metrics."""
        status_table = Table.grid(expand=True)
        status_table.add_column(justify="left", ratio=1)
        status_table.add_column(justify="right", ratio=1)
        
        status_msg = Text(" EDR Agent Running", style=f"bold {CONFIG['colors']['primary']}")
        if self.state.paused:
            status_msg.append(" [PAUSED]", style="bold yellow")
        
        counters = Text()
        counters.append("THREATS: ", style=CONFIG["colors"]["accent"])
        counters.append(str(self.state.threat_count), style=f"bold {CONFIG['colors']['warning']}")
        counters.append(" | ", style=CONFIG["colors"]["primary"])
        counters.append("SAFE: ", style=CONFIG["colors"]["accent"])
        counters.append(str(self.state.safe_count), style=f"bold {CONFIG['colors']['primary']}")
        
        status_table.add_row(status_msg, counters)
        self.layout["status"].update(Panel(status_table, border_style=CONFIG["colors"]["primary"], title="[STATUS]", title_align="left", box=box.SQUARE))

    def _render_main(self) -> None:
        """Renders the scrolling log of monitored network and process events."""
        log_panel_text = Text()
        visible_count = CONFIG["ui"]["visible_lines"]
        
        with self.state.log_lock:
            # surgical read of log buffer to avoid UI stutter
            logs_copy = list(self.state.logs)
            visible_logs = logs_copy[-visible_count:] if len(logs_copy) > visible_count else logs_copy
        
        for line in visible_logs:
            log_panel_text.append(line)
            log_panel_text.append("\n")
            
        self.layout["main"].update(Panel(log_panel_text, border_style=CONFIG["colors"]["primary"], title="[REAL-TIME MONITOR]", title_align="left", box=box.SQUARE))

    def _render_footer(self) -> None:
        """Renders system metrics (CPU, MEM) and heartbeat progress."""
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
        except Exception as e:
            logger.warning(f"Failed to fetch psutil metrics: {e}")
            cpu = 0.0
            mem = 0.0
            
        footer_grid = Table.grid(expand=True)
        footer_grid.add_column(justify="left", ratio=1)
        footer_grid.add_column(justify="right", ratio=1)
        
        uptime = int(time.time() - self.state.start_time)
        metrics = Text(f"Uptime: {uptime}s | SYS CPU: {cpu}% | SYS MEM: {mem}%", style=CONFIG["colors"]["accent"])
        
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, complete_style=CONFIG["colors"]["accent"], finished_style=CONFIG["colors"]["accent"]),
            console=self.console
        )
        progress.add_task("Core Heartbeat", total=100, completed=(time.time() * 25) % 100)
        
        footer_grid.add_row(metrics, progress)
        self.layout["footer"].update(Panel(footer_grid, border_style=CONFIG["colors"]["primary"], box=box.SQUARE))

class DataPipeline:
    """
    Manages the lifecycle of the SentryTop telemetry stream.
    
    What: Handles subprocess execution, parsing, and data injection.
    Why: Ensure that slow I/O reads do not block the UI render thread.
    How: Uses background daemon threads to continuously read stdout/stderr from the java correlation engine.
    """
    def __init__(self, state: CLIState, mock: bool = False) -> None:
        """
        Initializes the pipeline.
        
        Args:
            state (CLIState): Global state object to update.
            mock (bool): If true, skips process execution and generates synthetic data.
        """
        self.state = state
        self.mock = mock
        self.process: Optional[subprocess.Popen] = None
        self.ansi_strip = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        logger.info(f"DataPipeline initialized. Mock mode: {self.mock}")

    def initialize(self) -> None:
        """Starts telemetry threads or the mock generator."""
        if self.mock:
            logger.info("Initializing DataPipeline in MOCK mode.")
            threading.Thread(target=self._mock_generator, daemon=True, name="MockGenThread").start()
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        if os.getuid() == 0:
            env["NOSUDO"] = "1"

        try:
            self.process = subprocess.Popen(
                [CONFIG["paths"]["engine_script"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=script_dir,
                env=env,
                errors='replace' # Handle encoding issues safely
            )
            logger.info(f"Subprocess started with PID: {self.process.pid}")
            # Dedicated threads for stdout/stderr to prevent pipe blocking
            threading.Thread(target=self._pipe_reader, args=(self.process.stdout, "stdout"), daemon=True, name="StdOutThread").start()
            threading.Thread(target=self._pipe_reader, args=(self.process.stderr, "stderr"), daemon=True, name="StdErrThread").start()
        except Exception as e:
            logger.critical(f"Pipeline initiation failed: {e}")
            raise RuntimeError(f"Could not execute {CONFIG['paths']['engine_script']}: {e}")

    def _pipe_reader(self, pipe: Any, stream_name: str) -> None:
        """
        Reads from a pipe and forwards lines to the parser.
        
        Args:
            pipe: The subprocess output stream (stdout or stderr).
            stream_name (str): Identifier for logging purposes.
        """
        try:
            for line in iter(pipe.readline, ''):
                if not self.state.running: 
                    break
                if line:
                    self._process_payload(line)
        except ValueError as e:
            logger.error(f"Pipe stream {stream_name} closed or invalid: {e}")
        except Exception as e:
            logger.error(f"Error reading {stream_name}: {e}")

    def _process_payload(self, line: str) -> None:
        """
        Parses a telemetry line, removes ANSI codes, categorizes it, and updates state logs.
        
        Args:
            line (str): Raw string line from the correlator.
        """
        clean_text = self.ansi_strip.sub('', line).strip()
        if not clean_text: 
            return
            
        styled = Text(clean_text)
        is_threat = any(tag in clean_text for tag in CONFIG["threat_keywords"])
        is_safe = any(tag in clean_text for tag in CONFIG["safe_keywords"])
        
        if is_threat:
            self.state.threat_count += 1
            styled.stylize(f"bold {CONFIG['colors']['warning']}")
            # Beep sound (using ASCII bell)
            try:
                sys.stdout.write('\a')
                sys.stdout.flush()
            except Exception as e:
                logger.debug(f"Failed to play bell sound: {e}")
                
        elif is_safe:
            self.state.safe_count += 1
            styled.stylize(CONFIG["colors"]["accent"])
            if not self.state.verbose: 
                return
        elif clean_text.startswith("   └──"):
            styled.stylize(CONFIG["colors"]["accent"])
        else:
            styled.stylize(CONFIG["colors"]["primary"])

        if not self.state.paused:
            with self.state.log_lock:
                self.state.logs.append(styled)

    def _mock_generator(self) -> None:
        """Internal stress-test and validation generator for offline testing."""
        threat_samples = CONFIG["mock"]["threat_samples"]
        safe_samples = CONFIG["mock"]["safe_samples"]
        
        while self.state.running:
            time.sleep(random.uniform(CONFIG["mock"]["latency_min"], CONFIG["mock"]["latency_max"]))
            if random.random() < CONFIG["mock"]["threat_rate"]:
                sample = random.choice(threat_samples)
                self._process_payload(sample)
                self._process_payload(f"   └── Detail: Process mapping established for PID {random.randint(1000, 9999)}")
            else:
                self._process_payload(random.choice(safe_samples))

    def terminate(self) -> None:
        """Gracefully shuts down background processes to prevent zombie processes."""
        if self.process:
            logger.info("Terminating DataPipeline subprocess.")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning("Subprocess did not terminate gracefully, forcing kill.")
                self.process.kill()

class InputController:
    """
    Manages raw terminal input for interactive commands.
    
    What: Listens for keystrokes without blocking the main render loop.
    Why: Required for hotkey support (pause, verbose toggle, quit) in a live terminal environment.
    How: Temporarily sets terminal to cbreak mode and polls stdin.
    """
    def __init__(self, state: CLIState) -> None:
        """Initializes controller with reference to the global state."""
        self.state = state

    def run_loop(self) -> None:
        """Captures keystrokes in a non-blocking daemon thread."""
        logger.info("InputController thread started.")
        try:
            orig_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except termios.error as e:
            logger.warning(f"Could not set tty attributes (likely not a real terminal): {e}")
            return
            
        try:
            while self.state.running:
                # Use select with timeout to allow thread to exit cleanly when running becomes False
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key == 'q': 
                        logger.info("Quit hotkey pressed.")
                        self.state.running = False
                    elif key == 'p': 
                        self.state.paused = not self.state.paused
                        logger.info(f"Paused state toggled to: {self.state.paused}")
                    elif key == 'v': 
                        self.state.verbose = not self.state.verbose
                        logger.info(f"Verbose state toggled to: {self.state.verbose}")
        except Exception as e:
            logger.error(f"Input controller encountered an error: {e}")
        finally:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
            except termios.error:
                pass

def execute_glitch(console: Console) -> None:
    """
    Renders the retro terminal glitch animation on startup.
    
    Args:
        console (Console): The rich console instance to print to.
    """
    chars = "0123456789ABCDEF!@#$%^&*()_+-=[]{}|;':\",./<>?"
    for _ in range(CONFIG["ui"]["glitch_steps"]):
        line = "".join(random.choice(chars) for _ in range(120))
        console.print(Text(line, style=f"bold {CONFIG['colors']['primary']}"), end="\r")
        time.sleep(CONFIG["ui"]["glitch_delay"])
        console.clear()

def main() -> None:
    """Entry point for SentryTop CLI."""
    state = CLIState()
    console = Console()
    
    logger.info("SentryTop CLI starting sequence initialized.")
    mock_active = "--mock" in sys.argv

    # Authentication validation for real execution
    if not mock_active and os.getuid() != 0 and os.environ.get("NOSUDO") != "1":
        console.print("[bold yellow]SentryTop Sensor requires root privileges.[/bold yellow]")
        console.print("Authenticating for kernel polling access...")
        try:
            subprocess.run(["sudo", "-v"], check=True)
            logger.info("Sudo authentication successful.")
        except subprocess.CalledProcessError:
            logger.critical("Sudo authentication failed.")
            console.print("[bold red]Authentication failed. Terminating.[/bold red]")
            return

    # Startup Sequence
    try:
        execute_glitch(console)
    except Exception as e:
        logger.warning(f"Glitch animation failed: {e}")

    ui = SentryTopUI(console, state)
    pipeline = DataPipeline(state, mock=mock_active)
    input_ctrl = InputController(state)
    
    try:
        pipeline.initialize()
    except Exception as e:
        console.print(f"[bold red]FATAL ERROR: {e}[/bold red]")
        return

    # Start input listener in background
    threading.Thread(target=input_ctrl.run_loop, daemon=True, name="InputThread").start()

    # Main Render Loop
    try:
        with Live(ui.layout, refresh_per_second=CONFIG["ui"]["refresh_rate"], screen=True) as live:
            while state.running:
                # Watchdog check for pipeline process failures
                if not mock_active and pipeline.process and pipeline.process.poll() is not None:
                    logger.error(f"Pipeline process died unexpectedly with code {pipeline.process.returncode}")
                    break
                
                try:
                    live.update(ui.render_tick())
                except ConsoleError as e:
                    logger.warning(f"Console rendering error (possible terminal resize): {e}")
                except Exception as e:
                    logger.error(f"Unhandled render error: {e}")
                    
                time.sleep(1.0 / CONFIG["ui"]["refresh_rate"])
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main loop: {e}")
    finally:
        state.running = False
        pipeline.terminate()
        console.clear()
        console.print(f"[bold {CONFIG['colors']['primary']}]SentryTop CLI: Operational shutdown complete.[/bold {CONFIG['colors']['primary']}]")
        logger.info("SentryTop CLI shutdown complete.")

if __name__ == "__main__":
    main()
