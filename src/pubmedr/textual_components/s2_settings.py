# pubmedr/textual_components/s2_settings.py

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import Vertical


class S2screenSettings(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("This is Screen 2: Settings (Placeholder)")
