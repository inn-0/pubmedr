from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, Input, Static, TabbedContent, TabPane
from textual.containers import Vertical
from pubmedr.textual_components.s1_setup import S1screenSetup


class PubMedR(App):
    """Demo app showing proper nesting of screens in tabs"""

    CSS = """
    TabbedContent {
        height: auto;
    }
    TabPane {
        padding: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.cache = {}
        self.timestamp_uid = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Setup", id="setup"):
                with Vertical():  # Wrap in Vertical for proper layout
                    yield S1screenSetup()
            with TabPane("Search", id="search"):
                yield Vertical(
                    Label("Search Configuration"),
                    Input(placeholder="Enter search terms..."),
                )
            with TabPane("Results", id="results"):
                yield Vertical(
                    Label("Search Results"),
                    Static("No results yet..."),
                )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the app on startup"""
        self.title = "PubMed Research Assistant"


if __name__ == "__main__":
    app = PubMedR()
    app.run()
