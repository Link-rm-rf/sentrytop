from .base import BaseMode
from ..utils.constants import COLOR_ACCENT, COLOR_PRIMARY, COLOR_CRITICAL, COLOR_WARNING

class LogViewerMode(BaseMode):
    def __init__(self, app):
        super().__init__(app)
        self.name = "LOGS"
        self.selected_idx = 0
        self.scroll_offset = 0

    def handle_input(self, key):
        alerts = self.app.db.get_alerts(limit=100)
        if not alerts: return
        
        if key.name == 'KEY_UP' or key == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
            if self.selected_idx < self.scroll_offset:
                self.scroll_offset = self.selected_idx
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(alerts) - 1, self.selected_idx + 1)
            max_rows = self.term.height - 10
            if self.selected_idx >= self.scroll_offset + max_rows:
                self.scroll_offset = self.selected_idx - max_rows + 1

    def render(self):
        # 1. Header
        alerts = self.app.db.get_alerts(limit=100)
        subtitle = f"Historical Alerts: {len(alerts)}"
        self.renderer.draw_header("Alert Log", subtitle)

        # 2. Table Header
        header_y = 2
        col_header = f"  {'TIMESTAMP':<20} {'TYPE':<18} {'PROCESS':<15} {'THREAT'}"
        print(self.renderer.move_to(2, header_y) + self.term.bold(col_header), end='', flush=False)
        print(self.renderer.move_to(2, header_y + 1) + "─"*(self.term.width-4), end='', flush=False)

        # 3. Log Table
        max_rows = self.term.height - 10
        visible_alerts = alerts[self.scroll_offset : self.scroll_offset + max_rows]

        for i, a in enumerate(visible_alerts):
            idx = i + self.scroll_offset
            color = self.renderer.get_color("green")
            prefix = "  "
            if idx == self.selected_idx:
                color = self.renderer.term.bold_bright_green
                prefix = "> "
            
            # alert index mapping: id, ts, type, pid, proc, ip, port, threat, info
            ts = a[1].split('T')[-1].split('.')[0] if 'T' in a[1] else a[1]
            line = f"{prefix}{ts:<20} {a[2]:<18} {a[4][:13]:<15} {a[7]}"
            
            if a[7] == 'CRITICAL' and idx != self.selected_idx:
                color = self.renderer.get_color("red")
            elif a[7] == 'WARN' and idx != self.selected_idx:
                color = self.renderer.get_color("yellow")

            # Truncate
            line = line[:self.term.width - 4]
            print(self.renderer.move_to(2, i + header_y + 2) + color(line), end='', flush=False)

        # Clear remaining lines
        for i in range(len(visible_alerts), max_rows):
            print(self.renderer.move_to(2, i + header_y + 2) + " " * (self.term.width - 4), end='', flush=False)

        # 4. Detail Panel
        if alerts and self.selected_idx < len(alerts):
            a = alerts[self.selected_idx]
            y = self.term.height - 4
            print(self.renderer.move_to(0, y) + "╠" + "═"*(self.term.width-2) + "╣", end='', flush=False)
            detail = f" Info: {a[8]} | PID: {a[3]} | Dest: {a[5]}:{a[6]} "
            print(self.renderer.move_to(2, y+1) + self.renderer.get_color("green")(detail), end='', flush=False)

