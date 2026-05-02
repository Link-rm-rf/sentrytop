from blessed import Terminal
from ..utils.constants import COLOR_PRIMARY, COLOR_BG, COLOR_ACCENT

class RenderEngine:
    def __init__(self):
        self.term = Terminal()
        self.last_width = 0
        self.last_height = 0

    def clear(self):
        """Full screen clear."""
        print(self.term.home + self.term.clear, end='', flush=True)

    def begin_frame(self):
        print(self.term.home + self.term.clear, end='', flush=False)

    def end_frame(self):
        print('', end='', flush=True)

    def draw_header(self, title: str, subtitle: str = ""):
        """Draws a consistent header at the top of the screen."""
        header = self.term.move_xy(0, 0)
        header_text = f" SENTRYTOP v1.1.0 | {title.upper()}"
        if subtitle:
            header_text += f" | {subtitle}"
        
        # We need to construct the line with color
        full_line = header_text + " " * max(0, self.term.width - len(header_text))
        header += self.term.bold(self.term.bright_green_on_black(full_line))
        print(header, end='', flush=False)
        return 1

    def draw_footer(self, left_text: str, right_text: str):
        """Draws a consistent footer at the bottom of the screen."""
        y = self.term.height - 1
        footer = self.term.move_xy(0, y)
        
        clean_left = f" {left_text}"
        clean_right = f"{right_text} "
        padding = self.term.width - len(clean_left) - len(clean_right)
        
        full_line = clean_left
        if padding > 0:
            full_line += " " * padding
        full_line += clean_right
        
        footer += self.term.bold(self.term.bright_green_on_black(full_line))
        print(footer, end='', flush=False)

    def move_to(self, x: int, y: int):
        return self.term.move_xy(x, y)

    def get_color(self, color_name: str):
        if color_name == "dark_green": return self.term.green
        if color_name == "red": return self.term.bright_red
        if color_name == "yellow": return self.term.bright_yellow
        return self.term.bright_green

    def render_shadow_text(self, x: int, y: int, text: str, fg_color, bg_color=None, shadow_color=None, shadow_dx=2, shadow_dy=1):
        if shadow_color is None:
            shadow_color = self.term.green
        
        # Draw shadow
        shadow_line = self.move_to(x + shadow_dx, y + shadow_dy) + shadow_color(text)
        print(shadow_line, end='', flush=False)
        
        # Draw foreground
        fg = fg_color if not bg_color else bg_color(fg_color)
        fg_line = self.move_to(x, y) + fg(text)
        print(fg_line, end='', flush=False)

    def render_centered_ascii(self, ascii_art: list, y_offset: int, fg_color, shadow_color=None):
        art_height = len(ascii_art)
        
        # Draw shadow first
        if shadow_color:
            sy = y_offset + 1
            for line in ascii_art:
                sx = (self.term.width - len(line)) // 2 + 2
                if sx < 0: sx = 0
                if sy < self.term.height:
                    print(self.move_to(sx, sy) + shadow_color(line), end='', flush=False)
                sy += 1

        # Draw foreground second
        y = y_offset
        for line in ascii_art:
            x = (self.term.width - len(line)) // 2
            if x < 0: x = 0
            if y < self.term.height:
                print(self.move_to(x, y) + fg_color(line), end='', flush=False)
            y += 1
        
        return y_offset + art_height
