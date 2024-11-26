# pubmedr/textual_components/s2_settings.py

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import (
    Label,
    Input,
    Button,
    Checkbox,
    RadioButton,
    RadioSet,
    Collapsible,
    Select,
)
from textual.containers import Vertical, Horizontal
import pubmedr.data_store as data_store
from pubmedr.data_models import (
    S2datamodelSettings,
    EnumDateRange,
    EnumTextAvailability,
    S2datamodelSettingsSimple,
    S2datamodelSettingsSimpleAdvanced,
)


class S2screenSettings(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Search Settings", id="settings_title")
            # Toggle between Simple and Advanced
            with Horizontal():
                yield Label("Mode:")
                with RadioSet(id="mode_toggle"):
                    yield RadioButton("Simple", id="simple", value=True)
                    yield RadioButton("Advanced", id="advanced")
            # Simple Settings
            with Vertical(id="simple_settings"):
                yield Label("Keywords:")
                yield Input(placeholder="Enter keywords...", id="keywords")
                yield Label("Author:")
                yield Input(placeholder="Enter author name...", id="author")
                yield Label("Date Range:")
                date_options = [
                    (EnumDateRange.LAST_1_YEAR.value, EnumDateRange.LAST_1_YEAR.value),
                    (EnumDateRange.LAST_5_YEARS.value, EnumDateRange.LAST_5_YEARS.value),
                    (EnumDateRange.LAST_10_YEARS.value, EnumDateRange.LAST_10_YEARS.value),
                    (EnumDateRange.CUSTOM.value, EnumDateRange.CUSTOM.value),
                ]
                yield Select(options=date_options, id="date_range")
                # Custom Date Range Inputs
                with Horizontal(id="custom_date_inputs"):
                    yield Input(placeholder="Start Year", id="start_year")
                    yield Input(placeholder="End Year", id="end_year")
                yield Label("Text Availability:")
                text_options = [
                    (EnumTextAvailability.ALL.value, "All"),
                    (EnumTextAvailability.ABSTRACT.value, "Abstracts"),
                    (EnumTextAvailability.FREE_FULL_TEXT.value, "Free Full Text"),
                    (EnumTextAvailability.FULL_TEXT.value, "Full Text"),
                ]
                yield Select(options=text_options, id="text_availability")
                yield Label("Exclusions (comma-separated):")
                yield Input(placeholder="Terms, authors, journals...", id="exclusions")
            # Advanced Settings
            with Collapsible(title="Advanced Settings", collapsed=True, id="advanced_settings"):
                yield Checkbox("Enable Complex Boolean Logic", id="complex_boolean")
                yield Label("First Author:")
                yield Input(placeholder="Enter first author...", id="first_author")
                yield Label("Last Author:")
                yield Input(placeholder="Enter last author...", id="last_author")
                yield Label("Substance Name:")
                yield Input(placeholder="Enter substance name...", id="substance_name")
                yield Label("Proximity Search Terms:")
                yield Input(placeholder="Enter terms...", id="proximity_search_terms")
                yield Label("Proximity Distance:")
                yield Input(placeholder="Enter distance...", id="proximity_distance")
                # Additional advanced fields can be added here
            yield Button("Generate Queries", id="generate_queries")
            # Chat Interface
            yield Label("Chat with LLM:")
            yield Input(placeholder="Enter your message...", id="chat_input")
            yield Button("Send to LLM", id="send_to_llm")

    def refresh_from_data_store(self) -> None:
        data_store.refresh_widget_from_model(self, data_store.s2_settings_data)


print(S2datamodelSettings, S2datamodelSettingsSimple, S2datamodelSettingsSimpleAdvanced)
