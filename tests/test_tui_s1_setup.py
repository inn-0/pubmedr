from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from pubmedr.textual_components.s1_setup import S1screenSetup
from pubmedr.utils import load_cache


class TestS1App(App):
    """Test app for S1screenSetup with proper cache initialization"""

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.cache = load_cache()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(S1screenSetup())
        yield Footer()

    async def on_mount(self) -> None:
        """Handle app start up"""
        if not self.cache.get("gsheet_id"):
            self.bell()
            self.log.warning("No Google Sheet ID found in cache")


if __name__ == "__main__":
    app = TestS1App()
    app.run()
