# s1_setup.py

import re
from typing import cast

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label
from textual.worker import Worker

import pubmedr.data_store as data_store
from pubmedr.data_models import S1Setup
from pubmedr.gdrive import write_all_data
from pubmedr.textual_components.textual_utils import notify_error, notify_operation_status, open_url_in_browser
from pubmedr.utils import save_cache

# from typing import cast, TYPE_CHECKING

# if TYPE_CHECKING:
#     from pubmedr.main import PubMedR


def format_gsheet_url(gsheet_id: str) -> str:
    """Format a Google Sheet ID into a full URL."""
    return f"https://docs.google.com/spreadsheets/d/{gsheet_id}/edit?usp=sharing"


def extract_gsheet_id(url_or_id: str) -> str:
    """Extract the Google Sheet ID from a URL or return the ID if already bare."""
    # Match the full ID pattern, handling various URL formats
    pattern = r"(?:spreadsheets/d/|^)([a-zA-Z0-9-_]+)(?:/|$|/edit|\?)"
    match = re.search(pattern, url_or_id.strip())
    return match.group(1) if match else url_or_id.strip()


class S1screenSetup(Widget):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Google Sheet ID:")
            yield Input(placeholder="Enter Google Sheet ID...", id="s1_gsheet_id")
            yield Label("Researcher Background:")
            yield Input(placeholder="Describe your background...", id="s1_researcher_background")
            yield Label("Specific Research Goal:")
            yield Input(
                placeholder="Enter your specific research goal...",
                id="s1_researcher_goal",
            )
            yield Button("SAVE Setup", id="save_setup")
            yield Button("Open Google Sheet", id="open_database")

    async def on_mount(self) -> None:
        """Initialize fields from cache and data store"""
        app = cast("PubMedApp", self.app)
        gsheet_id = app.cache.get("gsheet_id", "")

        if gsheet_id:
            # Display as URL but store as ID
            url = format_gsheet_url(gsheet_id)
            self.query_one("#s1_gsheet_id", Input).value = url

            # If we have existing setup data in the store, use it
            if data_store.s1_setup_data:
                setup = data_store.s1_setup_data
                self.query_one("#s1_researcher_background", Input).value = setup.s1_researcher_background
                self.query_one("#s1_researcher_goal", Input).value = setup.s1_researcher_goal

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save button press"""
        if event.button.id == "save_setup":
            await self.save_setup()
        elif event.button.id == "open_database":
            gsheet_id = extract_gsheet_id(self.query_one("#s1_gsheet_id", Input).value)
            if gsheet_id:
                url = format_gsheet_url(gsheet_id)
                open_url_in_browser(url)
            else:
                self.app.bell()
                self.app.log("No Google Sheet ID found")

    @work(thread=True, exclusive=True)
    def save_to_gsheet(self, sheet_id: str) -> tuple[bool, str | None]:
        """Worker function to save to Google Sheet"""
        try:
            return write_all_data(sheet_id=sheet_id, sheet_name="data")
        except Exception as e:
            notify_error(self.app, f"Failed to save to Google Sheet: {str(e)}")
            return False, str(e)

    async def save_setup(self) -> None:
        """Save setup data to cache, data store, and Google Sheet"""
        app = cast("PubMedApp", self.app)

        # Extract ID from URL if needed
        gsheet_input = self.query_one("#s1_gsheet_id", Input).value.strip()
        gsheet_id = extract_gsheet_id(gsheet_input)

        setup_data = S1Setup(
            s1_gsheet_id=gsheet_id,
            s1_researcher_background=self.query_one("#s1_researcher_background", Input).value.strip(),
            s1_researcher_goal=self.query_one("#s1_researcher_goal", Input).value.strip(),
        )

        if not gsheet_id:
            notify_error(self.app, "Google Sheet ID is required")
            return

        try:
            data_store.s1_setup_data = setup_data
            app.cache["gsheet_id"] = gsheet_id
            save_cache(app.cache)
            self.save_to_gsheet(gsheet_id)

            notify_operation_status(
                self.app,
                True,
                "Local settings",
                success_msg="Settings Saved ✨",
            )

        except Exception as e:
            notify_error(self.app, f"Error saving settings: {str(e)}", "Setup save")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes"""
        if event.worker.name == "save_to_gsheet":
            if event.state.value == "SUCCESS":
                result = event.worker.result
                if result is not None:
                    success, error = result
                    notify_operation_status(
                        self.app,
                        success,
                        "Google Sheet",
                        success_msg="Settings saved to Google Sheet ✨",
                        error_msg=error or "Failed to save to Google Sheet",
                    )
                else:
                    notify_error(self.app, "No result from Google Sheet save operation")
            elif event.state.value == "ERROR":
                notify_error(self.app, f"Error in save operation: {event.worker.error}")

    def refresh_from_data_store(self) -> None:
        data_store.refresh_widget_from_model(self, data_store.s1_setup_data)
