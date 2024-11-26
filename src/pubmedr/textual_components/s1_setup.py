# s1_setup.py

from textual import work
from textual.worker import Worker
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Input, Label, Button
from textual.containers import Vertical
import pubmedr.data_store as data_store
from pubmedr.data_models import S1datamodelSetup
from pubmedr.utils import save_cache
from pubmedr.gdrive import write_all_data
from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    from pubmedr.main import PubMedApp


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
            yield Button("Save", id="save_setup")

    async def on_mount(self) -> None:
        """Initialize fields from cache and data store"""
        app = cast("PubMedApp", self.app)
        gsheet_id = app.cache.get("gsheet_id", "")

        if gsheet_id:
            self.query_one("#s1_gsheet_id", Input).value = gsheet_id

            # If we have existing setup data in the store, use it
            if data_store.s1_setup_data:
                setup = data_store.s1_setup_data
                self.query_one("#s1_researcher_background", Input).value = setup.s1_researcher_background
                self.query_one("#s1_researcher_goal", Input).value = setup.s1_researcher_goal

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save button press"""
        if event.button.id == "save_setup":
            await self.save_setup()

    @work(thread=True, exclusive=True)
    def save_to_gsheet(self, sheet_id: str) -> tuple[bool, str | None]:
        """Worker function to save to Google Sheet"""
        try:
            return write_all_data(sheet_id=sheet_id, sheet_name="data")
        except Exception:
            return False, None

    async def save_setup(self) -> None:
        """Save setup data to cache, data store, and Google Sheet"""
        app = cast("PubMedApp", self.app)

        # Get values from inputs
        setup_data = S1datamodelSetup(
            s1_gsheet_id=self.query_one("#s1_gsheet_id", Input).value.strip(),
            s1_researcher_background=self.query_one("#s1_researcher_background", Input).value.strip(),
            s1_researcher_goal=self.query_one("#s1_researcher_goal", Input).value.strip(),
        )

        if not setup_data.s1_gsheet_id:
            self.app.log.error("Google Sheet ID is required")
            return
        data_store.s1_setup_data = setup_data
        app.cache["gsheet_id"] = setup_data.s1_gsheet_id
        save_cache(app.cache)
        self.save_to_gsheet(setup_data.s1_gsheet_id)
        self.app.bell()
        self.app.log.info("Setup save initiated")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes"""
        if event.worker.name == "save_to_gsheet":
            if event.state.value == "SUCCESS":
                result = event.worker.result
                if result is not None:
                    success, _ = result
                    if success:
                        self.app.log.info("Setup saved successfully to Google Sheet")
                    else:
                        self.app.log.error("Failed to save to Google Sheet")
                else:
                    self.app.log.error("No result from Google Sheet save operation")
            elif event.state.value == "ERROR":
                self.app.log.error(f"Error saving to Google Sheet: {event.worker.error}")
