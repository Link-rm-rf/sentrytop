from abc import ABC, abstractmethod
from ..utils.logger import logger

class BaseMode(ABC):
    def __init__(self, app):
        self.app = app
        self.term = app.renderer.term
        self.renderer = app.renderer
        self.name = "BASE"

    @abstractmethod
    def handle_input(self, key):
        pass

    def update(self):
        """Called every frame before render. Modes can override this."""
        pass

    def on_enter(self):
        """Called when switching to this mode. Modes can override this."""
        pass

    @abstractmethod
    def render(self):
        """
        Render the current mode. 
        Each mode is responsible for drawing its main content area.
        The header and footer are handled by the main app.
        """
        pass

    def clear_screen(self):
        self.renderer.clear()

    def log_error(self, msg):
        logger.error(f"[{self.name}] {msg}")
