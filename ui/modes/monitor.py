from .base import BaseMode
from ..utils.constants import COLOR_PRIMARY, COLOR_ACCENT, COLOR_CRITICAL, COLOR_WARNING

class MonitorMode(BaseMode):
    def __init__(self, app):
        super().__init__(app)
        self.name = "MONITOR"
        self.paused = False
        self.selected_index = 0

    def handle_input(self, key):
        if key.lower() == 'p':
            self.paused = not self.paused
        elif key.name == 'KEY_UP' or key.lower() == 'k':
            self.selected_index = max(0, self.selected_index - 1)
        elif key.name == 'KEY_DOWN' or key.lower() == 'j':
            alerts_count = self.app.alert_queue.size
            self.selected_index = min(max(0, alerts_count - 1), self.selected_index + 1)
        elif key.lower() == 'c':
            self.app.alert_queue.clear()
            self.selected_index = 0

    def render(self):
        # 1. Header
        subtitle = f"Threats: {self.app.alert_queue.threat_count} | Safe: {self.app.alert_queue.safe_count}"
        if self.paused:
            subtitle += " [PAUSED]"
        self.renderer.draw_header("Monitor", subtitle)

        # 2. Split Screen - Top Half (Telemetry)
        stats = self.app.stats_cache.get_stats()
        split_y = self.term.height // 2
        
        telemetry_title = self.term.bold(self.renderer.get_color("green")("=== SYSTEM TELEMETRY ==="))
        print(self.renderer.move_to(2, 2) + telemetry_title, end='', flush=False)
        
        cpu_bar = f"CPU Usage:  [{'#' * int(stats.get('cpu', 0) / 2):<50}] {stats.get('cpu', 0)}%"
        mem_bar = f"MEM Usage:  [{'#' * int(stats.get('memory', 0) / 2):<50}] {stats.get('memory', 0)}%"
        print(self.renderer.move_to(2, 4) + self.renderer.get_color("green")(cpu_bar), end='', flush=False)
        print(self.renderer.move_to(2, 5) + self.renderer.get_color("green")(mem_bar), end='', flush=False)
        
        proc_count = len(stats.get('processes', []))
        conn_count = len(stats.get('connections', []))
        print(self.renderer.move_to(2, 7) + self.renderer.get_color("green")(f"Active Processes: {proc_count}   |   Active Connections: {conn_count}"), end='', flush=False)
        
        print(self.renderer.move_to(2, split_y - 1) + self.term.bold(self.renderer.get_color("green")("=== SECURITY ALERTS ===")), end='', flush=False)

        # 3. Alerts List (Bottom Half)
        alerts = self.app.alert_queue.get_all()
        max_rows = self.term.height - split_y - 2 # Leave space for footer
        
        # Calculate viewport
        if not alerts:
            print(self.renderer.move_to(2, split_y + 1) + self.renderer.get_color("green")("Waiting for telemetry data..."), flush=False)
            return

        visible_alerts = alerts[-max_rows:]
        for i, alert in enumerate(visible_alerts):
            severity = alert.get('threat', 'SAFE').upper()
            color = self.renderer.get_color("green")
            if severity in ['CRITICAL', 'HIGH']:
                color = self.renderer.get_color("red")
            elif severity == 'WARN':
                color = self.renderer.get_color("yellow")
            
            timestamp = alert.get('timestamp', '').split('T')[-1].split('.')[0]
            line = f"[{timestamp}] [{severity}] {alert.get('type')}: {alert.get('process')} -> {alert.get('source_ip')}"
            
            # Truncate if too long
            if len(line) > self.term.width - 4:
                line = line[:self.term.width - 7] + "..."
                
            print(self.renderer.move_to(2, split_y + 1 + i) + color(line), end='', flush=False)

        # Clear remaining lines in content area if any
        for i in range(len(visible_alerts), max_rows):
            print(self.renderer.move_to(2, split_y + 1 + i) + " " * (self.term.width - 4), end='', flush=False)
