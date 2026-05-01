import psutil
import signal
import time
import os

class ProcessManagerMode:
    def __init__(self, app):
        self.app = app
        self.term = app.term
        self.selected_idx = 0
        self.scroll_offset = 0
        self.protected = ['systemd', 'sshd', 'nginx', 'kernel', 'init', 'systemd-', 'Xtigervnc', 'bash']
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
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(procs) - 1, self.selected_idx + 1)
        elif key.lower() == 'k':
            if procs:
                self.confirmation_pid = procs[self.selected_idx]['pid']

    def _kill_confirmed(self, pid):
        try:
            os.kill(pid, signal.SIGTERM)
            # Simple wait-and-check
            time.sleep(0.5)
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
            self.kill_result = f"[✓] PID {pid} Killed"
        except Exception as e:
            self.kill_result = f"[✗] Failed: {str(e)[:20]}"
        self.kill_result_time = time.time()

    def render(self):
        term = self.term
        print(term.home + term.green + "╔" + "═"*(term.width-2) + "╗")
        print(term.move_x(2) + "SENTRYTOP - PROCESS MANAGER")
        print("╠" + "═"*(term.width-2) + "╣")
        
        stats = self.app.stats_cache.get_stats()
        procs = stats['processes']
        
        # Table Header
        header = f"  {'PID':<8} {'PROCESS':<20} {'USER':<12} {'CPU%':<6} {'MEM%':<6} {'THREAT'}"
        print(term.move_x(2) + term.bold(header))
        print(term.move_x(2) + "─"*(term.width-4))

        max_rows = term.height - 12
        visible_procs = procs[self.scroll_offset : self.scroll_offset + max_rows]
        
        for i, p in enumerate(visible_procs):
            idx = i + self.scroll_offset
            color = term.green
            prefix = "  "
            if idx == self.selected_idx:
                color = term.cyan
                prefix = "> "
            
            # Mock threat score correlation for now
            alerts = self.app.db.get_alerts_for_pid(p['pid'])
            threat = "SAFE"
            if alerts:
                threat = "CRITICAL" if any(a[0] == 'CRITICAL' for a in alerts) else "WARN"
                if threat == "CRITICAL": color = term.red if idx != self.selected_idx else term.cyan

            line = f"{prefix}{p['pid']:<8} {p['name'][:18]:<20} {p['username'][:10]:<12} {p.get('cpu_percent', 0):<6} {p.get('memory_percent', 0):<6.1f} {threat}"
            print(term.move_x(2) + color(line))

        # Detail Panel
        self._render_detail(procs)
        
        # Confirmation Overlay
        if self.confirmation_pid:
            self._render_confirmation()

        if self.kill_result and time.time() - self.kill_result_time < 3:
            print(term.move_y(term.height-2) + term.move_x(2) + term.yellow(self.kill_result))

    def _render_detail(self, procs):
        if not procs or self.selected_idx >= len(procs): return
        p = procs[self.selected_idx]
        term = self.term
        y = term.height - 6
        print(term.move_y(y) + "╠" + "═"*(term.width-2) + "╣")
        print(term.move_y(y+1) + term.move_x(2) + term.cyan(f"Selected: {p['name']} (PID: {p['pid']})"))
        
        is_protected = any(prot in p['name'] for prot in self.protected)
        prot_msg = term.red("⚠️ SYSTEM PROCESS") if is_protected else term.green("USER PROCESS")
        print(term.move_x(2) + f"Status: {prot_msg} | PPID: {p['ppid']}")
        
    def _render_confirmation(self):
        term = self.term
        p_name = "Unknown"
        stats = self.app.stats_cache.get_stats()
        for p in stats['processes']:
            if p['pid'] == self.confirmation_pid:
                p_name = p['name']
                break
        
        box_w, box_h = 40, 5
        x, y = (term.width - box_w) // 2, (term.height - box_h) // 2
        
        print(term.move(y, x) + term.red("╔" + "═"*(box_w-2) + "╗"))
        print(term.move(y+1, x) + term.red("║") + f" KILL {p_name} ({self.confirmation_pid})? ".center(box_w-2) + term.red("║"))
        print(term.move(y+2, x) + term.red("║") + " [Y] Confirm  [N] Cancel ".center(box_w-2) + term.red("║"))
        print(term.move(y+3, x) + term.red("╚" + "═"*(box_w-2) + "╝"))
