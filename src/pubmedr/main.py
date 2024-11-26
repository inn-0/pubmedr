# main.py

from textual.app import App, ComposeResult
from textual.widgets import Header, TabbedContent, TabPane
from textual.containers import Vertical
from pubmedr.textual_components.s1_setup import S1screenSetup
from pubmedr.textual_components.s2_settings import S2screenSettings
from pubmedr.textual_components.s3_queries import S3screenQueries
from pubmedr.textual_components.s4_results import S4screenResults
from pubmedr.textual_components.s5_saved import S5screenSaved
from pubmedr.textual_components.textual_utils import CustomFooter
from pubmedr.utils import load_cache
from pubmedr.gdrive import read_last_entry
import pubmedr.data_store as data_store
from pubmedr.data_models import S1datamodelSetup


class PubMedR(App):
    CSS_PATH = None

    BINDINGS = [
        ("1", "show_tab('s1_setup')", "Setup"),
        ("2", "show_tab('s2_settings')", "Settings"),
        ("3", "show_tab('s3_queries')", "Queries"),
        ("4", "show_tab('s4_results')", "Results"),
        ("5", "show_tab('s5_saved')", "Saved"),
    ]

    def __init__(self):
        super().__init__()
        self.cache = load_cache()
        self.timestamp_uid: str | None = None

        # If no cached data_store contents, try loading from Google Sheet
        if "data_store_dump" not in self.cache:
            gsheet_id = self.cache.get("gsheet_id", "")
            if gsheet_id:
                try:
                    last_entry = read_last_entry(sheet_id=gsheet_id, sheet_name="data")
                    if last_entry:
                        # Store in data_store for components to access
                        data_store.s1_setup_data = S1datamodelSetup(
                            s1_gsheet_id=gsheet_id,
                            s1_researcher_background=last_entry.get("s1_researcher_background", ""),
                            s1_researcher_goal=last_entry.get("s1_researcher_goal", ""),
                        )
                        self.log.info("Loaded previous setup data from Google Sheet")
                except Exception as e:
                    self.log.error(f"Failed to load previous setup: {str(e)}")
        else:
            self.log.info("Loaded data from local cache")

    def on_mount(self) -> None:
        self.theme = "dracula"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with TabbedContent(id="main_tabs", initial="s1_setup"):
                with TabPane("[1] Setup", id="s1_setup"):
                    with Vertical():
                        yield S1screenSetup()
                with TabPane("[2] Settings", id="s2_settings"):
                    with Vertical():
                        yield S2screenSettings()
                with TabPane("[3] Queries", id="s3_queries"):
                    with Vertical():
                        yield S3screenQueries()
                with TabPane("[4] Results", id="s4_results"):
                    with Vertical():
                        yield S4screenResults()
                with TabPane("[5] Saved", id="s5_saved"):
                    with Vertical():
                        yield S5screenSaved()
            yield CustomFooter()

    def action_show_tab(self, tab: str) -> None:
        self.query_one("#main_tabs", TabbedContent).active = tab

    def refresh_footer(self):
        """Refresh the footer to update the timestamp display."""
        footer = self.query_one(CustomFooter)
        footer.refresh()


if __name__ == "__main__":
    app = PubMedR()
    app.run()
