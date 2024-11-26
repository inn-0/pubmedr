# pubmedr/textual_components/s4_results.py

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import Vertical
import pubmedr.data_store as data_store


class S4screenResults(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("This is Screen 4: Results (Placeholder)")

    def refresh_from_data_store(self) -> None:
        data_store.refresh_widget_from_model(self, data_store.s4_results_data)
