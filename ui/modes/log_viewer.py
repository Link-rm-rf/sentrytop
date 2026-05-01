class LogViewerMode:
    def __init__(self, app):
        self.app = app
        self.term = app.term
        self.selected_idx = 0

    def handle_input(self, key):
        alerts = self.app.db.get_alerts(limit=50)
        if not alerts: return
        
        if key.name == 'KEY_UP' or key == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(alerts) - 1, self.selected_idx + 1)

    def render(self):
        term = self.term
        print(term.home + term.green + "╔" + "═"*(term.width-2) + "╗")
        print(term.move_x(2) + "SENTRYTOP - ALERT LOG")
        print("╠" + "═"*(term.width-2) + "╣")

        alerts = self.app.db.get_alerts(limit=50)
        
        header = f"  {'TIMESTAMP':<20} {'TYPE':<18} {'PROCESS':<15} {'THREAT'}"
        print(term.move_x(2) + term.bold(header))
        print(term.move_x(2) + "─"*(term.width-4))

        max_rows = term.height - 10
        visible_alerts = alerts[:max_rows]

        for i, a in enumerate(visible_alerts):
            color = term.green
            prefix = "  "
            if i == self.selected_idx:
                color = term.cyan
                prefix = "> "
            
            # alert index mapping: id, ts, type, pid, proc, ip, port, threat, info
            ts = a[1].split('T')[1].split('.')[0]
            line = f"{prefix}{ts:<20} {a[2]:<18} {a[4][:13]:<15} {a[7]}"
            
            if a[7] == 'CRITICAL': color = term.red if i != self.selected_idx else term.cyan
            elif a[7] == 'WARN': color = term.yellow if i != self.selected_idx else term.cyan

            print(term.move_x(2) + color(line))
        
        # Detail panel
        if alerts and self.selected_idx < len(alerts):
            a = alerts[self.selected_idx]
            y = term.height - 4
            print(term.move_y(y) + "╠" + "═"*(term.width-2) + "╣")
            print(term.move_y(y+1) + term.move_x(2) + term.cyan(f"Info: {a[8]} | PID: {a[3]} | Dest: {a[5]}:{a[6]}"))
