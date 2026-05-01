class NetworkInsightMode:
    def __init__(self, app):
        self.app = app
        self.term = app.term
        self.selected_idx = 0

    def handle_input(self, key):
        stats = self.app.stats_cache.get_stats()
        conns = stats['connections']
        if not conns: return

        if key.name == 'KEY_UP' or key == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
        elif key.name == 'KEY_DOWN' or key == 'j':
            self.selected_idx = min(len(conns) - 1, self.selected_idx + 1)

    def render(self):
        term = self.term
        print(term.home + term.green + "╔" + "═"*(term.width-2) + "╗")
        print(term.move_x(2) + "SENTRYTOP - NETWORK INSIGHT")
        print("╠" + "═"*(term.width-2) + "╣")

        stats = self.app.stats_cache.get_stats()
        conns = stats['connections']

        header = f"  {'LOCAL ADDR':<25} {'REMOTE ADDR':<25} {'STATE':<12} {'THREAT'}"
        print(term.move_x(2) + term.bold(header))
        print(term.move_x(2) + "─"*(term.width-4))

        max_rows = term.height - 10
        visible_conns = conns[:max_rows]

        for i, c in enumerate(visible_conns):
            color = term.green
            prefix = "  "
            if i == self.selected_idx:
                color = term.cyan
                prefix = "> "
            
            local = f"{c.laddr.ip}:{c.laddr.port}"
            remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "*:*"
            
            # Simple threat correlation for remote IP
            threat = "SAFE"
            if c.raddr:
                # Mock: in a real app, query database or intel cache
                pass

            line = f"{prefix}{local:<25} {remote:<25} {c.status:<12} {threat}"
            print(term.move_x(2) + color(line))
        
        # Detail panel
        if conns and self.selected_idx < len(conns):
            c = conns[self.selected_idx]
            y = term.height - 4
            print(term.move_y(y) + "╠" + "═"*(term.width-2) + "╣")
            remote_ip = c.raddr.ip if c.raddr else "N/A"
            print(term.move_y(y+1) + term.move_x(2) + term.cyan(f"Remote IP: {remote_ip} | FD: {c.fd} | PID: {c.pid or 'N/A'}"))
