# s2_settings.py

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import Number
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Select,
)

import pubmedr.data_store as data_store
from pubmedr.data_models import EnumDateRange, EnumGender, EnumSpecies, EnumTextAvailability
from pubmedr.data_models import S2datamodelSettingsAdvanced as S2s
from pubmedr.data_models import S2datamodelSettingsSimple as S2a
from pubmedr.data_models import S2datamodelSettings

# Helper function to get field descriptions for tooltips
def get_field_description(model_class, field_name):
    try:
        return model_class.model_fields[field_name].description
    except AttributeError:
        return model_class.__fields__[field_name].field_info.description


class S2screenSettings(Widget):
    CSS = """
    Input.-valid {
        border: tall $success 60%;
    }
    Input.-valid:focus {
        border: tall $success;
    }
    Input.-invalid {
        border: tall $error 60%;
    }
    Input.-invalid:focus {
        border: tall $error;
    }
    Input {
        margin: 1 1;
    }
    Label {
        margin: 1 2;
    }
    #advanced_settings {
        visibility: hidden;
    }

    #advanced_settings.show-advanced {
        visibility: visible;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Search Settings", id="settings_title")
            # Toggle between Simple and Advanced
            with Horizontal():
                yield Label("Mode:")
                with RadioSet(id="mode_toggle"):
                    yield RadioButton("Simple", id="simple_mode", value=True)
                    yield RadioButton("Advanced", id="advanced_mode")
            # Simple Settings (always visible)
            with Vertical(id="simple_settings"):
                self.compose_simple_settings()
            # Advanced Settings (Initially hidden via CSS)
            with Vertical(id="advanced_settings"):
                self.compose_advanced_settings()
            # Chat Interface
            yield Label("Chat with LLM:")
            yield Input(placeholder="Enter your message...", id="chat_input")
            yield Button("Send to LLM", id="send_to_llm")
        # Footer with hotkeys
        yield Footer()

    def compose_simple_settings(self):
        yield Label("Keywords:")
        yield Input(
            placeholder="Enter keywords...",
            id="keywords",
            tooltip=get_field_description(S2a, "keywords"),
        )
        yield Label("Author:")
        yield Input(
            placeholder="Enter author name...",
            id="author",
            tooltip=get_field_description(S2a, "author"),
        )
        yield Label("Date Range:")
        date_options = [
            (EnumDateRange.LAST_1_YEAR.value, EnumDateRange.LAST_1_YEAR.value),
            (EnumDateRange.LAST_5_YEARS.value, EnumDateRange.LAST_5_YEARS.value),
            (EnumDateRange.LAST_10_YEARS.value, EnumDateRange.LAST_10_YEARS.value),
            (EnumDateRange.CUSTOM.value, EnumDateRange.CUSTOM.value),
        ]
        yield Select(options=date_options, id="date_range")
        # Custom Date Range Inputs (Initially hidden)
        with Horizontal(id="custom_date_inputs"):
            yield Input(
                placeholder="Start Year",
                id="start_year",
                validators=[Number(minimum=1750, maximum=2026)],
                tooltip=get_field_description(S2a, "start_year"),
            )
            yield Input(
                placeholder="End Year",
                id="end_year",
                validators=[Number(minimum=1750, maximum=2026)],
                tooltip=get_field_description(S2a, "end_year"),
            )
        yield Label("Text Availability:")
        text_options = [
            (EnumTextAvailability.ALL.value, "All"),
            (EnumTextAvailability.ABSTRACT.value, "Abstracts"),
            (EnumTextAvailability.FREE_FULL_TEXT.value, "Free Full Text"),
            (EnumTextAvailability.FULL_TEXT.value, "Full Text"),
        ]
        yield Select(options=text_options, id="text_availability")
        yield Label("Exclusions:")
        yield Input(
            placeholder="Terms, authors, journals...",
            id="exclusions",
            tooltip=get_field_description(S2a, "exclusions"),
        )

    def compose_advanced_settings(self):
        yield Checkbox("Enable Complex Boolean Logic", id="complex_boolean")
        yield Label("First Author:")
        yield Input(
            placeholder="Enter first author...",
            id="first_author",
            tooltip=get_field_description(S2s, "first_author"),
        )
        yield Label("Last Author:")
        yield Input(
            placeholder="Enter last author...",
            id="last_author",
            tooltip=get_field_description(S2s, "last_author"),
        )
        yield Label("Substance Name:")
        yield Input(
            placeholder="Enter substance name...",
            id="substance_name",
            tooltip=get_field_description(S2s, "substance_name"),
        )
        yield Label("Proximity Search Terms:")
        yield Input(
            placeholder="Enter terms...",
            id="proximity_search_terms",
            tooltip=get_field_description(S2s, "proximity_search_terms"),
        )
        yield Label("Proximity Distance:")
        yield Input(
            placeholder="Enter distance...",
            id="proximity_distance",
            validators=[Number(minimum=0)],
            tooltip=get_field_description(S2s, "proximity_distance"),
        )
        yield Label("Species:")
        species_options = [
            (EnumSpecies.HUMAN.value, "Humans"),
            (EnumSpecies.ANIMAL.value, "Other Animals"),
            (EnumSpecies.BOTH.value, "Both"),
        ]
        yield Select(options=species_options, id="species")
        yield Label("Gender:")
        gender_options = [
            (EnumGender.MALE.value, "Male"),
            (EnumGender.FEMALE.value, "Female"),
            (EnumGender.BOTH.value, "Both"),
        ]
        yield Select(options=gender_options, id="gender")
        yield Label("MeSH Terms:")
        yield Input(
            placeholder="Enter MeSH terms...",
            id="mesh_terms",
            tooltip=get_field_description(S2s, "mesh_terms"),
        )
        yield Label("Publication Types:")
        yield Input(
            placeholder="Enter publication types...",
            id="publication_types",
            tooltip=get_field_description(S2s, "publication_types"),
        )
        yield Label("Unique Identifiers:")
        yield Input(
            placeholder="Enter unique identifiers...",
            id="unique_identifiers",
            tooltip=get_field_description(S2s, "unique_identifiers"),
        )
        yield Label("Affiliation Includes:")
        yield Input(
            placeholder="Enter affiliations to include...",
            id="affiliation_includes",
            tooltip=get_field_description(S2s, "affiliation_includes"),
        )
        yield Label("Affiliation Excludes:")
        yield Input(
            placeholder="Enter affiliations to exclude...",
            id="affiliation_excludes",
            tooltip=get_field_description(S2s, "affiliation_excludes"),
        )
        yield Label("Article Types:")
        yield Input(
            placeholder="Enter article types...",
            id="article_types",
            tooltip=get_field_description(S2s, "article_types"),
        )
        yield Label("Result Limit:")
        yield Input(
            placeholder="Enter result limit...",
            id="result_limit",
            validators=[Number(minimum=1)],
            tooltip=get_field_description(S2s, "result_limit"),
        )

    @on(RadioSet.Changed, "#mode_toggle")
    def mode_toggle_changed(self, event: RadioSet.Changed) -> None:
        """Handle mode toggle between Simple and Advanced."""
        advanced_settings = self.query_one("#advanced_settings")

        if event.pressed.id == "advanced_mode":
            advanced_settings.add_class("show-advanced")
        else:
            advanced_settings.remove_class("show-advanced")

    @on(Select.Changed, "#date_range")
    def date_range_changed(self, event: Select.Changed) -> None:
        """Handle date range selection to show/hide custom date inputs."""
        custom_date_inputs = self.query_one("#custom_date_inputs", Horizontal)
        if event.value == EnumDateRange.CUSTOM.value:
            custom_date_inputs.visible = True
        else:
            custom_date_inputs.visible = False
        self.refresh()

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        """Handle input change events to update validation styling."""
        input_widget = event.input
        # Skip validation for chat input
        if input_widget.id == "chat_input":
            return

        validation_result = event.validation_result
        if validation_result and validation_result.is_valid:
            input_widget.add_class("-valid")
            input_widget.remove_class("-invalid")
        elif validation_result:
            input_widget.add_class("-invalid")
            input_widget.remove_class("-valid")

    def refresh_from_data_store(self) -> None:
        """Refresh widget contents from the data store."""
        data_store.refresh_widget_from_model(self, data_store.s2_settings_data)


print(S2datamodelSettings, S2s, S2a)
