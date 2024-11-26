# gdrive.py

from gspread.auth import service_account_from_dict as gspread_init
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import CellFormat, format_cell_range, set_column_width
from pubmedr import config
import pubmedr.data_store as data_store
import pandas as pd
from datetime import datetime


logger = config.custom_logger(__name__)


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


def write_all_data(sheet_id: str, sheet_name: str = "data") -> tuple[bool, str | None]:
    try:
        gc = gspread_init(config.GOOGLE_CLOUD_CREDENTIALS)
        worksheet = gc.open_by_key(sheet_id).worksheet(sheet_name)
        existing_df = get_as_dataframe(worksheet).dropna(how="all")

        # Combine all data models into a single dictionary
        combined_data = {}
        if data_store.s1_setup_data:
            combined_data.update(data_store.s1_setup_data.dict())
        if data_store.s2_settings_data:
            combined_data.update(data_store.s2_settings_data.dict())
        if data_store.s3_queries_data:
            combined_data.update(data_store.s3_queries_data.dict())
        if data_store.s4_results_data:
            combined_data.update(data_store.s4_results_data.dict())
        if data_store.s5_saved_data:
            combined_data.update(data_store.s5_saved_data.dict())

        # Add timestamp UID
        timestamp_uid = datetime.now().isoformat()
        combined_data["timestamp_uid"] = timestamp_uid

        # Convert to DataFrame and append to existing data
        new_row = pd.DataFrame([combined_data])
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
