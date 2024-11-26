# pubmedr/textual_components/s5_saved.py

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import Vertical


class S5screenSaved(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("This is Screen 5: Saved Papers (Placeholder)")
