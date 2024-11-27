# pubmedr/textual_components/s5_saved.py

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable

from pubmedr.gdrive import read_all_entries
from pubmedr.textual_components.textual_utils import (
    load_settings,
    notify_operation_status,
    open_url_in_browser,
)


class S5screenSaved(Widget):
    """Screen 5: Saved Papers"""

    BINDINGS = [
        ("enter", "open_url", "Open URL"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield DataTable(id="saved_data_table")
            yield Button("LOAD Settings from Selected", id="load_settings")
            yield Button("Refresh Data", id="refresh_data")
            yield Button("Open Google Sheet", id="open_database")

    async def on_mount(self) -> None:
        """Do not load data on mount to prevent focus issues."""
        pass

    async def load_data(self):
        if hasattr(self, "loading_data") and self.loading_data:
            return
        self.loading_data = True

        app = self.app
        gsheet_id = app.cache.get("gsheet_id", "")
        if not gsheet_id:
            app.log("No Google Sheet ID found. Please enter it in the Setup screen.")
            self.loading_data = False
            return

        entries = read_all_entries(sheet_id=gsheet_id, sheet_name="data")
        if not entries:
            app.log("No saved data found in Google Sheet.")
            self.loading_data = False
            return

        self.entries = entries
        data_table = self.query_one(DataTable)
        data_table.clear(columns=True)

        # Get columns, excluding s1_gsheet_id
        columns = [col for col in entries[0].keys() if col != "s1_gsheet_id"]
        data_table.add_columns(*columns)

        # Add rows
        for idx, entry in enumerate(entries):
            row_values = [str(entry.get(col, "")) for col in columns]
            data_table.add_row(*row_values, key=str(idx))

        data_table.zebra_stripes = True
        data_table.show_header = True
        data_table.cursor_type = "cell"
        data_table.can_focus = True

        self.loading_data = False

    async def on_show(self) -> None:
        await self.load_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses without causing focus issues."""
        if event.button.id == "load_settings":
            # Prevent multiple activations
            if hasattr(self, "processing_recreate") and self.processing_recreate:
                return
            self.processing_recreate = True

            data_table = self.query_one(DataTable)
            coordinate = data_table.cursor_coordinate
            row_index = coordinate.row
            if row_index < 0:
                self.app.log("No row selected.")
                self.app.bell()
                self.processing_recreate = False
                return
            entry = self.entries[row_index]
            # Remove 'timestamp_uid' from entry if present
            entry.pop("timestamp_uid", None)
            load_settings(self.app, entry)
            self.processing_recreate = False
            notify_operation_status(self.app, True, "Data load", "Settings Loaded ✨")
        elif event.button.id == "refresh_data":
            # Prevent multiple activations
            if hasattr(self, "processing_refresh") and self.processing_refresh:
                return
            self.processing_refresh = True
            await self.load_data()
            self.processing_refresh = False
        elif event.button.id == "open_database":
            gsheet_id = self.app.cache.get("gsheet_id", "")
            if gsheet_id:
                url = f"https://docs.google.com/spreadsheets/d/{gsheet_id}/edit#gid=0"
                open_url_in_browser(url)
            else:
                self.app.bell()
                self.app.log("No Google Sheet ID found")

    def action_open_url(self) -> None:
        """Handle Enter key press to open URL if applicable."""
        data_table = self.query_one(DataTable)
        coordinate = data_table.cursor_coordinate
        if coordinate is None or coordinate.row == 0:  # Check for None coordinate
            return
        cell_value = data_table.get_cell_at(coordinate)
        if isinstance(cell_value, str) and cell_value.startswith("http"):
            open_url_in_browser(cell_value)
        else:
            self.app.log("Selected cell does not contain a URL.")
            self.app.bell()
