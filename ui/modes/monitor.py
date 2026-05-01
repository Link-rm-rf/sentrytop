from collections import deque

class MonitorMode:
    def __init__(self, app):
        self.app = app
        self.term = app.term
        self.logs = deque(maxlen=100)
        self.paused = False

    def handle_input(self, key):
        if key.lower() == 'p':
            self.paused = not self.paused

    def render(self):
        term = self.term
        # Get new alerts from FIFO reader
        new_alerts = self.app.fifo_reader.get_new_alerts()
        if not self.paused:
            for alert in new_alerts:
                timestamp = alert['timestamp'].split('T')[1].split('.')[0]
                line = f"[{timestamp}] [{alert['threat']}] {alert['type']}: {alert['process']} -> {alert['source_ip']}:{alert['port']}"
                self.logs.append(line)

        # Header
        print(term.home + term.green + "╔" + "═"*(term.width-2) + "╗")
        header_text = " SENTRYTOP - REAL-TIME MONITOR "
        if self.paused: header_text += "[PAUSED]"
        print(term.move_x(2) + term.bold(header_text))
        print("╠" + "═"*(term.width-2) + "╣")

        # Log feed
        max_rows = term.height - 5
        visible_logs = list(self.logs)[-max_rows:]
        for i, line in enumerate(visible_logs):
            color = term.green
            if "[CRITICAL]" in line: color = term.red
            elif "[WARN]" in line: color = term.yellow
            elif "[ALERT]" in line: color = term.cyan
            
            print(term.move_y(i + 3) + term.move_x(2) + color(line))
