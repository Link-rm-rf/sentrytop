import os
import signal
import time
import psutil
from .base import BaseMode
from ..utils.constants import PROTECTED_PROCESSES, COLOR_ACCENT, COLOR_CRITICAL, COLOR_PRIMARY

class ProcessManagerMode(BaseMode):
    def __init__(self, app):
        super().__init__(app)
        self.name = "PROCESS"
        self.selected_idx = 0
        self.scroll_offset = 0
        self.confirmation_pid = None
        self.kill_result = None
        self.kill_result_time = 0

    def handle_input(self, key):
        stats = self.app.stats_cache.get_stats()
        procs = stats['processes']
        
        if self.confirmation_pid:
            if key.lower() == 'y':
                self._kill_confirmed(self.confirmation_pid)
                self.confirmation_pid = None
            elif key.lower() == 'n' or key.name == 'KEY_ESCAPE':
                self.confirmation_pid = None
            return

        if key.name == 'KEY_UP' or key == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
            if self.selected_idx < self.scroll_offset:
                self.scroll_offset = self.selected_idx
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(procs) - 1, self.selected_idx + 1)
            max_rows = self.term.height - 12
            if self.selected_idx >= self.scroll_offset + max_rows:
                self.scroll_offset = self.selected_idx - max_rows + 1
        elif key.lower() == 'k':
            if procs and self.selected_idx < len(procs):
                self.confirmation_pid = procs[self.selected_idx]['pid']
        elif key.lower() == 'r':
            # Stats are auto-updated by StatsCache, but we could trigger something here if needed
            pass

    def _kill_confirmed(self, pid):
        try:
            # Safety check
            try:
                p = psutil.Process(pid)
                if any(prot in p.name() for prot in PROTECTED_PROCESSES):
                    self.kill_result = f"[!] BLOCKED: System Process"
                    self.kill_result_time = time.time()
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
            self.kill_result = f"[✓] PID {pid} Killed"
            self.app.logger.info(f"Process {pid} killed by user.")
        except Exception as e:
            self.kill_result = f"[✗] Failed: {str(e)[:20]}"
            self.log_error(f"Kill failed for PID {pid}: {e}")
        self.kill_result_time = time.time()

    def render(self):
        stats = self.app.stats_cache.get_stats()
        procs = stats['processes']
        
        # 1. Header
        subtitle = f"Total: {len(procs)}"
        self.renderer.draw_header("Process Manager", subtitle)

        # 2. Table Header
        header_y = 2
        col_header = f"  {'PID':<8} {'PROCESS':<20} {'USER':<12} {'CPU%':<6} {'MEM%':<6} {'THREAT'}"
        print(self.renderer.move_to(2, header_y) + self.term.bold(col_header), end='', flush=False)
        print(self.renderer.move_to(2, header_y + 1) + "─"*(self.term.width-4), end='', flush=False)

        # 3. Process Table
        max_rows = self.term.height - 12
        visible_procs = procs[self.scroll_offset : self.scroll_offset + max_rows]
        
        for i, p in enumerate(visible_procs):
            idx = i + self.scroll_offset
            color = self.renderer.get_color("green")
            prefix = "  "
            if idx == self.selected_idx:
                color = self.renderer.term.bold_bright_green
                prefix = "> "
            
            # Simple threat correlation
            threat = "SAFE"
            alerts = self.app.db.get_alerts_for_pid(p['pid'])
            if alerts:
                threat = "CRITICAL" if any(a[0] == 'CRITICAL' for a in alerts) else "WARN"
                if threat == "CRITICAL" and idx != self.selected_idx:
                    color = self.renderer.get_color("red")

            line = f"{prefix}{p['pid']:<8} {p['name'][:18]:<20} {p['username'][:10]:<12} {p.get('cpu_percent', 0):<6} {p.get('memory_percent', 0):<6.1f} {threat}"
            # Truncate
            line = line[:self.term.width - 4]
            print(self.renderer.move_to(2, i + header_y + 2) + color(line), end='', flush=False)

        # Clear remaining lines
        for i in range(len(visible_procs), max_rows):
            print(self.renderer.move_to(2, i + header_y + 2) + " " * (self.term.width - 4), end='', flush=False)

        # 4. Detail Panel
        self._render_detail(procs)
        
        # 5. Overlays
        if self.confirmation_pid:
            self._render_confirmation()

        if self.kill_result and time.time() - self.kill_result_time < 3:
            print(self.renderer.move_to(2, self.term.height-2) + self.renderer.get_color("yellow")(self.kill_result), end='', flush=False)

    def _render_detail(self, procs):
        if not procs or self.selected_idx >= len(procs): return
        p = procs[self.selected_idx]
        y = self.term.height - 6
        print(self.renderer.move_to(0, y) + "╠" + "═"*(self.term.width-2) + "╣", end='', flush=False)
        
        detail = f" Selected: {p['name']} (PID: {p['pid']}) | PPID: {p['ppid']} "
        print(self.renderer.move_to(2, y+1) + self.renderer.get_color("green")(detail), end='', flush=False)
        
        is_protected = any(prot in p['name'] for prot in PROTECTED_PROCESSES)
        prot_msg = self.renderer.get_color("red")("⚠️ SYSTEM PROCESS") if is_protected else self.renderer.get_color("green")("USER PROCESS")
        print(self.renderer.move_to(2, y+2) + f" Status: {prot_msg}", end='', flush=False)
        
    def _render_confirmation(self):
        p_name = "Unknown"
        stats = self.app.stats_cache.get_stats()
        for p in stats['processes']:
            if p['pid'] == self.confirmation_pid:
                p_name = p['name']
                break
        
        box_w, box_h = 40, 5
        x, y = (self.term.width - box_w) // 2, (self.term.height - box_h) // 2
        
        print(self.renderer.move_to(x, y) + self.term.red("╔" + "═"*(box_w-2) + "╗"), end='', flush=False)
        print(self.renderer.move_to(x, y+1) + self.term.red("║") + f" KILL {p_name} ({self.confirmation_pid})? ".center(box_w-2) + self.term.red("║"), end='', flush=False)
        print(self.renderer.move_to(x, y+2) + self.term.red("║") + " [Y] Confirm  [N] Cancel ".center(box_w-2) + self.term.red("║"), end='', flush=False)
        print(self.renderer.move_to(x, y+3) + self.term.red("╚" + "═"*(box_w-2) + "╝"), end='', flush=False)
