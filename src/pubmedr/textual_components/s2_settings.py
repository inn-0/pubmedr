# pubmedr/textual_components/s2_settings.py

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label
import pubmedr.data_store as data_store
from textual.containers import Vertical


class S2screenSettings(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("This is Screen 2: Settings (Placeholder)")

    def refresh_from_data_store(self) -> None:
        data_store.refresh_widget_from_model(self, data_store.s2_settings_data)
