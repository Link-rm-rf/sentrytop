"""
SentryTop v1.1 - ASCII Art & Banner Handling
"""

BANNER = r"""
███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ 
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗
███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝     ██║   ██║   ██║██╔═══╝ 
███████║███████╗██║ ╚████║   ██║   ██║  ██║   ██║      ██║   ╚██████╔╝██║     
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝
"""

def get_centered_banner(term_width: int) -> str:
    """Returns the banner centered for the current terminal width."""
    lines = BANNER.strip("\n").split("\n")
    centered_lines = []
    for line in lines:
        padding = max(0, (term_width - len(line)) // 2)
        centered_lines.append(" " * padding + line)
    return "\n".join(centered_lines)
