import time
from .base import BaseMode
from ..utils.constants import MODE_MONITOR, MODE_PROCESS, MODE_NETWORK, MODE_LOGS

class MainMenuMode(BaseMode):
    def __init__(self, app):
        super().__init__(app)
        self.name = "MAIN MENU"
        self.selected_idx = 0
        self.reveal_start = 0
        self.reveal_duration = 1.0 # seconds
        self.options = [
            ("[1]  MONITOR CENTER", MODE_MONITOR),
            ("[2]  PROCESS MANAGER", MODE_PROCESS),
            ("[3]  NETWORK INSIGHT", MODE_NETWORK),
            ("[4]  ALERT LOGS", MODE_LOGS),
            ("[Q]  EXIT SENTRYTOP", "QUIT")
        ]

    def handle_input(self, key):
        if key.name == 'KEY_UP' or str(key).lower() == 'k':
            self.selected_idx = max(0, self.selected_idx - 1)
        elif key.name == 'KEY_DOWN' or str(key).lower() == 'j':
            self.selected_idx = min(len(self.options) - 1, self.selected_idx + 1)
        elif key.name == 'KEY_ENTER':
            target = self.options[self.selected_idx][1]
            if target == "QUIT":
                self.app.running = False
            else:
                self.app.current_mode_key = target
                self.app.renderer.clear()
                
    def on_enter(self):
        # Reset animation when entering mode
        self.reveal_start = time.time()

    def render(self):
        # Clear screen
        print(self.renderer.term.home + self.renderer.term.clear + self.renderer.term.green_on_black, end='', flush=False)

        width = self.term.width
        height = self.term.height
        
        # We start with some blank lines
        y = 2
        
        # Header
        header = "SENTRYTOP v1.1.0 - ADVANCED SYSTEM THREAT MONITOR"
        header_x = max(0, (width - len(header)) // 2)
        print(self.renderer.move_to(header_x, y) + self.term.green(header), end='', flush=False)
        y += 1
        
        logo_art = [
            r"  ███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ",
            r"  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗",
            r"  ███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝",
            r"  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝     ██║   ██║   ██║██╔═══╝ ",
            r"  ███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║      ██║   ╚██████╔╝██║     ",
            r"  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝     "
        ]
        
        for line in logo_art:
            art_x = max(0, (width - len(line)) // 2)
            print(self.renderer.move_to(art_x, y) + self.term.green(line), end='', flush=False)
            y += 1
            
        # Blank lines
        y += 2
        
        # Menu box
        box_width = min(width - 4, 60)
        x_offset = max(0, (width - box_width) // 2)
        
        # Top border
        print(self.renderer.move_to(x_offset, y) + self.term.green("┌" + "─" * (box_width - 2) + "┐"), end='', flush=False)
        y += 1
        
        # Header row
        header_text = "SELECT MODE"
        padding = (box_width - 2 - len(header_text)) // 2
        header_row = "│" + " " * padding + header_text + " " * (box_width - 2 - padding - len(header_text)) + "│"
        print(self.renderer.move_to(x_offset, y) + self.term.green(header_row), end='', flush=False)
        y += 1
        
        # Separator
        print(self.renderer.move_to(x_offset, y) + self.term.green("├" + "─" * (box_width - 2) + "┤"), end='', flush=False)
        y += 1
        
        empty_line = "│" + " " * (box_width - 2) + "│"
        
        # Menu items
        print(self.renderer.move_to(x_offset, y) + self.term.green(empty_line), end='', flush=False)
        y += 1
        
        options_data = [
            ("1", "MONITOR CENTER", "Real-time alerts, threats, and system security overview"),
            ("2", "PROCESS MANAGER", "View running processes and manage system resources"),
            ("3", "NETWORK INSIGHT", "Monitor connections, ports, and network threats"),
            ("4", "ALERT LOGS", "View historical alerts and export logs"),
            ("Q", "QUIT SENTRYTOP", "Exit the application")
        ]
        
        for i, (key, title, desc) in enumerate(options_data):
            prefix = "> " if i == self.selected_idx else "  "
            line1 = f"{prefix}[{key}] {title}"
            line2 = f"    {desc}"
            
            line1_padded = line1.ljust(box_width - 2)
            line2_padded = line2.ljust(box_width - 2)
            
            # Format row
            if i == self.selected_idx:
                print(self.renderer.move_to(x_offset, y) + self.term.green("│") + self.term.bold_green(line1_padded) + self.term.green("│"), end='', flush=False)
                y += 1
                print(self.renderer.move_to(x_offset, y) + self.term.green("│") + self.term.green(line2_padded) + self.term.green("│"), end='', flush=False)
                y += 1
            else:
                print(self.renderer.move_to(x_offset, y) + self.term.green("│") + self.term.green(line1_padded) + self.term.green("│"), end='', flush=False)
                y += 1
                print(self.renderer.move_to(x_offset, y) + self.term.green("│") + self.term.green(line2_padded) + self.term.green("│"), end='', flush=False)
                y += 1
                
            if i < len(options_data) - 1:
                print(self.renderer.move_to(x_offset, y) + self.term.green(empty_line), end='', flush=False)
                y += 1
        
        # Bottom border
        print(self.renderer.move_to(x_offset, y) + self.term.green("└" + "─" * (box_width - 2) + "┘"), end='', flush=False)
