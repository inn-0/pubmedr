# textual_utils.py

import webbrowser
from datetime import datetime
from typing import TYPE_CHECKING, cast

from pydantic import ValidationError
from rich.text import Text
from textual.widgets import Button, Footer

import pubmedr.data_store as data_store
from pubmedr.data_models import (
    S1Setup,
    S2Query,
    S2Settings,
    S4Results,
    S5SavedResult,
)
from pubmedr.utils import save_cache

if TYPE_CHECKING:
    from pubmedr.main import PubMedR


def open_url_in_browser(url: str):
    """Open the given URL in the default web browser."""
    webbrowser.open(url)


class SaveButton(Button):
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast("PubMedR", self.app)
        # Get gsheet_id from cache or default
        gsheet_id = app.cache.get("gsheet_id", "")
        if not gsheet_id:
            await app.push_screen("s1_setup")  # Navigate to setup screen if ID is missing
            app.notify("No Google Sheet ID found. Please enter it in the Setup screen.")
            return
        from pubmedr.gdrive import write_all_data

        success, timestamp_uid = write_all_data(sheet_id=gsheet_id)
        if success:
            app.notify("Data saved successfully.")
            app.timestamp_uid = timestamp_uid
            app.refresh_footer()
        else:
            app.notify("Failed to save data.")


class CustomFooter(Footer):
    def render(self) -> Text:
        """Render the footer with timestamp and key bindings."""
        base_text = Text()
        for binding in self.app.BINDINGS:
            key_display = Text(f" {binding[0]} ", style="bold white on rgb(98,98,98)")
            description = Text(f" {binding[2]} ", style="dim white")
            base_text.append(key_display)
            base_text.append(description)

        # Add timestamp if available
        app = cast("PubMedR", self.app)
        timestamp_uid = getattr(app, "timestamp_uid", None)
        if timestamp_uid:
            timestamp = datetime.fromisoformat(timestamp_uid)
            time_str = f" Saved at {timestamp.strftime('%H:%M:%S')}"
            base_text.append(" " * 4)  # Add some spacing
            base_text.append(Text(time_str, style="bold white"))

        return base_text


def refresh_all_screens(app):
    """Refresh all screens to reflect new data_store values."""
    from pubmedr.textual_components.s1_setup import S1screenSetup
    from pubmedr.textual_components.s2_settings import S2screenSettings
    from pubmedr.textual_components.s3_queries import S3screenQueries
    from pubmedr.textual_components.s4_results import S4screenResults

    if s1_screen := app.query_one(S1screenSetup):
        s1_screen.refresh_from_data_store()
    if s2_screen := app.query_one(S2screenSettings):
        s2_screen.refresh_from_data_store()
    if s3_screen := app.query_one(S3screenQueries):
        s3_screen.refresh_from_data_store()
    if s4_screen := app.query_one(S4screenResults):
        s4_screen.refresh_from_data_store()
    # if s5_screen := app.query_one(S5screenSaved):
    #     s5_screen.refresh_from_data_store()


def load_settings(app, entry: dict):
    """Recreate settings by updating data_store and UI components."""

    data_model_classes = {
        "s1_setup_data": S1Setup,
        "s2_settings_data": S2Settings,
        "s2_queries_data": S2Query,
        "s4_results_data": S4Results,
        "s5_saved_data": S5SavedResult,
    }

    for model_name, model_class in data_model_classes.items():
        try:
            model_fields = model_class.__fields__.keys()
            model_data = {k: entry[k] for k in model_fields if k in entry}
            if model_data:
                model_instance = model_class(**model_data)
                setattr(data_store, model_name, model_instance)
            else:
                setattr(data_store, model_name, None)
        except ValidationError as e:
            app.log(f"Validation error for {model_name}: {e}")
            setattr(data_store, model_name, None)

    if data_store.s1_setup_data:
        app.cache["gsheet_id"] = data_store.s1_setup_data.s1_gsheet_id
        save_cache(app.cache)

    refresh_all_screens(app)

    app.log("Settings have been loaded from the selected entry.")
    app.bell()


def notify_operation_status(
    app,
    success: bool,
    operation_name: str,
    success_msg: str | None = None,
    error_msg: str | None = None,
    timeout: int = 5,
) -> None:
    """Show a toast notification for operation status.

    Args:
        app: The Textual app instance
        success: Whether the operation succeeded
        operation_name: Name of the operation (for default messages)
        success_msg: Optional custom success message
        error_msg: Optional custom error message
        timeout: Notification timeout in seconds
    """
    if success:
        app.notify(
            success_msg or f"{operation_name} completed ✨",
            title="Success",
            timeout=timeout,
        )
        app.log.info(f"{operation_name} completed")
    else:
        app.notify(
            error_msg or f"Failed to complete {operation_name}",
            title="Error",
            severity="error",
            timeout=timeout,
        )
        app.log.error(f"Failed to complete {operation_name}: {error_msg or 'unknown error'}")


def notify_error(
    app,
    error_msg: str,
    operation_name: str | None = None,
    timeout: int = 5,
) -> None:
    """Show an error toast notification.

    Args:
        app: The Textual app instance
        error_msg: The error message
        operation_name: Optional operation name for logging
        timeout: Notification timeout in seconds
    """
    app.notify(
        error_msg,
        title="Error",
        severity="error",
        timeout=timeout,
    )
    app.log.error(f"{operation_name + ': ' if operation_name else ''}{error_msg}")
