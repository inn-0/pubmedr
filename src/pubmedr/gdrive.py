# gdrive.py

from datetime import datetime
from typing import Any

import logfire
import pandas as pd
from gspread.auth import service_account_from_dict as gspread_init
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import CellFormat, format_cell_range, set_column_width

from pubmedr import config

logger = config.custom_logger(__name__)

_worksheet_cache = {}


def get_cached_worksheet(sheet_id: str, sheet_name: str = "data"):
    """Get or create cached worksheet connection."""
    cache_key = f"{sheet_id}:{sheet_name}"
    if cache_key not in _worksheet_cache:
        gc = gspread_init(config.GOOGLE_CLOUD_CREDENTIALS)
        _worksheet_cache[cache_key] = gc.open_by_key(sheet_id).worksheet(sheet_name)
    return _worksheet_cache[cache_key]


def format_worksheet(worksheet):
    # Format header row with bold and center alignment
    header_format = CellFormat(
        textFormat={"bold": True},
        horizontalAlignment="CENTER",
        wrapStrategy="CLIP",
    )
    format_cell_range(worksheet, "1:1", header_format)

    # Format data rows with wrapping
    data_format = CellFormat(wrapStrategy="CLIP")
    if worksheet.row_count > 1:
        format_cell_range(worksheet, f"2:{worksheet.row_count}", data_format)

    # Set column widths based on header text length (with some padding)
    for col, header in enumerate(worksheet.row_values(1), start=1):
        width = len(header) * 10 + 40  # Approximate pixel width based on text length
        col_letter = chr(64 + col)
        set_column_width(worksheet, f"{col_letter}:{col_letter}", width)


def write_all_data(
    sheet_id: str,
    data: dict[str, Any],
    sheet_name: str = "data",
) -> tuple[bool, str | None]:
    """Write data to Google Sheet, appending to existing data.

    Args:
        sheet_id: Google Sheet ID
        data: Dictionary of data to write
        sheet_name: Sheet name within the Google Sheet

    Returns:
        Tuple of (success, timestamp_uid)
    """
    try:
        worksheet = get_cached_worksheet(sheet_id, sheet_name)
        existing_df = get_as_dataframe(worksheet).dropna(how="all")

        # Add timestamp UID
        timestamp_uid = datetime.now().isoformat()
        data["timestamp_uid"] = timestamp_uid

        # Convert to DataFrame and append to existing data
        new_row = pd.DataFrame([data])
        new_df = pd.concat([existing_df, new_row], ignore_index=True)

        # Write back to the sheet
        set_with_dataframe(
            worksheet,
            new_df,
            include_index=False,
            include_column_header=True,
            resize=True,
        )
        format_worksheet(worksheet)
        return True, timestamp_uid
    except Exception as error:
        logger.error(f"Error writing data: {error}")
        return False, None


def read_last_entry(sheet_id: str, sheet_name: str = "data") -> dict | None:
    try:
        gc = gspread_init(config.GOOGLE_CLOUD_CREDENTIALS)
        worksheet = gc.open_by_key(sheet_id).worksheet(sheet_name)
        df = get_as_dataframe(worksheet).dropna(how="all")
        if not df.empty:
            # Get the last non-empty row
            last_row = df.iloc[-1:].to_dict(orient="records")[0]
            return last_row
        else:
            return None
    except Exception as error:
        logger.error(f"Error reading data: {error}")
        return None


def read_all_entries(sheet_id: str, sheet_name: str = "data") -> list[dict]:
    """Read all entries from the specified Google Sheet and return as a list of dictionaries."""
    try:
        gc = gspread_init(config.GOOGLE_CLOUD_CREDENTIALS)
        worksheet = gc.open_by_key(sheet_id).worksheet(sheet_name)
        df = get_as_dataframe(worksheet).dropna(how="all")
        if not df.empty:
            # Fill NA with empty strings to avoid serialization issues
            records = df.fillna("").to_dict(orient="records")
            return records
        else:
            return []
    except Exception as error:
        logger.error(f"Error reading all data: {error}")
        return []


def write_search_result(sheet_id: str, sheet_name: str, result_data: dict) -> tuple[bool, str | None]:
    """Write a single search result with its associated metadata to the sheet."""
    try:
        worksheet = get_cached_worksheet(sheet_id, sheet_name)
        existing_df = get_as_dataframe(worksheet).dropna(how="all")

        # Add timestamp
        timestamp_uid = datetime.now().isoformat()
        result_data["timestamp"] = timestamp_uid

        # Convert to DataFrame and append
        new_row = pd.DataFrame([result_data])
        new_df = pd.concat([existing_df, new_row], ignore_index=True)

        # Update the sheet
        set_with_dataframe(worksheet, new_df)
        format_worksheet(worksheet)
        return True, timestamp_uid
    except Exception as error:
        logger.error(f"Error writing search result: {error}")
        return False, None


def write_settings(sheet_id: str, settings_data: dict) -> tuple[bool, str | None]:
    """Write settings snapshot to Google Sheet."""
    with logfire.span("write_settings"):
        try:
            logger.info("Starting settings write", extra={"sheet_id": sheet_id})
            worksheet = get_cached_worksheet(sheet_id, "data")
            logger.info("Got worksheet")

            existing_df = get_as_dataframe(worksheet).dropna(how="all")
            logger.info("Got existing data", extra={"rows": len(existing_df)})

            # Add timestamp and type marker
            timestamp = datetime.now().isoformat()
            settings_data.update(
                {
                    "timestamp": timestamp,
                    "type": "settings_snapshot",
                }
            )

            # Convert to DataFrame and append
            new_row = pd.DataFrame([settings_data])
            new_df = pd.concat([existing_df, new_row], ignore_index=True)
            logger.info("Prepared new data", extra={"new_rows": len(new_df) - len(existing_df)})

            # Update sheet
            set_with_dataframe(worksheet, new_df)
            logger.info("Written to sheet")
            format_worksheet(worksheet)
            logger.info("Formatted worksheet")

            return True, timestamp
        except Exception as error:
            logger.error(
                "Error writing settings",
                exc_info=True,
                extra={
                    "error": str(error),
                    "sheet_id": sheet_id,
                    "data_size": len(str(settings_data)),
                },
            )
            return False, None


def read_latest_settings(sheet_id: str) -> dict | None:
    """Read most recent settings snapshot from Google Sheet."""
    try:
        worksheet = get_cached_worksheet(sheet_id, "data")
        df = get_as_dataframe(worksheet).dropna(how="all")

        if not df.empty:
            # Get latest settings snapshot
            settings_df = df[df["type"] == "settings_snapshot"]
            if not settings_df.empty:
                return settings_df.iloc[-1].to_dict()
        return None
    except Exception as error:
        logger.error(f"Error reading settings: {error}")
        return None
