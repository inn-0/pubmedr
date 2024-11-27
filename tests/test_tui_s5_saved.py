# test_tui_s5_saved.py

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from pubmedr.textual_components.s5_saved import S5screenSaved
from pubmedr.utils import load_cache


class TestS5App(App):
    """Test app for S5screenSaved with proper cache initialization"""

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.cache = load_cache()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(S5screenSaved())
        yield Footer()


if __name__ == "__main__":
    app = TestS5App()
    app.run()
