# textual_utils.py

from textual.widgets import Button, Footer
from rich.text import Text
from typing import TYPE_CHECKING, cast
from datetime import datetime

if TYPE_CHECKING:
    from pubmedr.main import PubMedApp


class SaveButton(Button):
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("PubMedApp", self.app)
        # Get gsheet_id from cache or default
        gsheet_id = app.cache.get("gsheet_id", "")
        if not gsheet_id:
            await app.push_screen("s1_setup")  # Navigate to setup screen if ID is missing
            await app.notify("No Google Sheet ID found. Please enter it in the Setup screen.")
            return
        from pubmedr.gdrive import write_all_data

        success, timestamp_uid = write_all_data(sheet_id=gsheet_id)
        if success:
            await app.notify("Data saved successfully.")
            app.timestamp_uid = timestamp_uid
            app.refresh_footer()
        else:
            await app.notify("Failed to save data.")


class CustomFooter(Footer):
    def render(self):
        app = cast("PubMedApp", self.app)
        timestamp_uid = getattr(app, "timestamp_uid", None)
        if timestamp_uid:
            # Format timestamp as HH:MM:SS
            timestamp = datetime.fromisoformat(timestamp_uid)
            time_str = timestamp.strftime("%H:%M:%S")
            # Display in the footer
            base_render = super().render()
            # Use Textual's markup to align to the right
            return Text.assemble(base_render, Text(" " * 10 + f"Saved at {time_str}", style="bold", justify="right"))
        else:
            return super().render()
