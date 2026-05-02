from .base import BaseMode
from ..utils.constants import COLOR_ACCENT, COLOR_PRIMARY, COLOR_CRITICAL

class NetworkInsightMode(BaseMode):
    def __init__(self, app):
        super().__init__(app)
        self.name = "NETWORK"
        self.selected_idx = 0
        self.scroll_offset = 0

    def handle_input(self, key):
        stats = self.app.stats_cache.get_stats()
        conns = stats['connections']
        if not conns: return

        if key.name == 'KEY_UP' or key == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
            if self.selected_idx < self.scroll_offset:
                self.scroll_offset = self.selected_idx
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(conns) - 1, self.selected_idx + 1)
            max_rows = self.term.height - 10
            if self.selected_idx >= self.scroll_offset + max_rows:
                self.scroll_offset = self.selected_idx - max_rows + 1

    def render(self):
        stats = self.app.stats_cache.get_stats()
        conns = stats['connections']

        # 1. Header
        subtitle = f"Active Connections: {len(conns)}"
        self.renderer.draw_header("Network Insight", subtitle)

        # 2. Table Header
        header_y = 2
        col_header = f"  {'LOCAL ADDR':<25} {'REMOTE ADDR':<25} {'STATE':<12} {'PID/PROC'}"
        print(self.renderer.move_to(2, header_y) + self.term.bold(col_header), end='', flush=False)
        print(self.renderer.move_to(2, header_y + 1) + "─"*(self.term.width-4), end='', flush=False)

        # 3. Connections Table
        max_rows = self.term.height - 10
        visible_conns = conns[self.scroll_offset : self.scroll_offset + max_rows]

        for i, c in enumerate(visible_conns):
            idx = i + self.scroll_offset
            color = self.renderer.get_color("green")
            prefix = "  "
            if idx == self.selected_idx:
                color = self.renderer.term.bold_bright_green
                prefix = "> "
            
            laddr = f"{c.laddr.ip}:{c.laddr.port}" if hasattr(c, 'laddr') else "N/A"
            raddr = f"{c.raddr.ip}:{c.raddr.port}" if hasattr(c, 'raddr') and c.raddr else "*:*"
            
            pid_info = f"{c.pid or 'N/A'}"
            # Try to find process name from stats
            proc_name = ""
            for p in stats['processes']:
                if p['pid'] == c.pid:
                    proc_name = f" [{p['name'][:10]}]"
                    break
            pid_info += proc_name

            line = f"{prefix}{laddr:<25} {raddr:<25} {c.status:<12} {pid_info}"
            # Truncate
            line = line[:self.term.width - 4]
            print(self.renderer.move_to(2, i + header_y + 2) + color(line), end='', flush=False)

        # Clear remaining lines
        for i in range(len(visible_conns), max_rows):
            print(self.renderer.move_to(2, i + header_y + 2) + " " * (self.term.width - 4), end='', flush=False)

        # 4. Detail Panel
        if conns and self.selected_idx < len(conns):
            c = conns[self.selected_idx]
            y = self.term.height - 4
            print(self.renderer.move_to(0, y) + "╠" + "═"*(self.term.width-2) + "╣", end='', flush=False)
            
            remote_ip = c.raddr.ip if hasattr(c, 'raddr') and c.raddr else "N/A"
            detail = f" Remote IP: {remote_ip} | FD: {getattr(c, 'fd', 'N/A')} | PID: {c.pid or 'N/A'} "
            print(self.renderer.move_to(2, y+1) + self.renderer.get_color("green")(detail), end='', flush=False)

