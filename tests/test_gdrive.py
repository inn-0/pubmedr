# test_gdrive.py

# for additional examples of using GDrive (e.g. formatting, Google Docs, Google Drive folders) go here (author's own filesystem):
# /mnt/c/Files/7Generosity_Career Old Job Files/InnoSwit.ch/A_product/Lewrick/A_Product/grrp_colleague_finder/tests/test_gdrive.py
# /mnt/c/Files/7Generosity_Career Old Job Files/InnoSwit.ch/A_product/Lewrick/A_Product/grrp_colleague_finder/src/classify_users_grrp.py


import pytest

import pubmedr.data_store as data_store
from pubmedr.data_models import S1Setup
from pubmedr.gdrive import read_all_entries, read_last_entry, write_all_data

SHEET_ID = "1iC_D0ggTRiHhr8EOl7Mi2HRYs7efzFZSRw6GqPUSC8s"
SHEET_NAME = "test_s1_setup"


@pytest.fixture
def test_setup_data():
    """Test data matching S1Setup model fields."""
    return S1Setup(
        s1_gsheet_id=SHEET_ID,
        s1_researcher_background="Test researcher with biology background",
        s1_researcher_goal="Find papers about CRISPR applications",
    )


def test_write_read_last_entry(test_setup_data):
    """Test writing and reading data from Google Sheet."""

    data_store.s1_setup_data = test_setup_data

    success, timestamp_uid = write_all_data(sheet_id=SHEET_ID, sheet_name=SHEET_NAME)
    assert success, "Failed to write setup data"
    assert timestamp_uid is not None, "Timestamp UID is None"

    result = read_last_entry(sheet_id=SHEET_ID, sheet_name=SHEET_NAME)
    assert result is not None, "Failed to read setup data"

    # Remove the 'timestamp_uid' before comparison
    result_data = result.copy()
    result_data.pop("timestamp_uid", None)

    assert result_data == test_setup_data.model_dump(), "Read data doesn't match written data"

    assert "timestamp_uid" in result, "Timestamp UID not found in result"


def test_read_all_entries():
    """Test reading all entries and their content from Google Sheet."""
    entries = read_all_entries(sheet_id=SHEET_ID, sheet_name=SHEET_NAME)
    assert isinstance(entries, list), "Entries should be a list"

    if entries:
        assert isinstance(entries[0], dict), "Each entry should be a dict"
        required_fields = ["timestamp_uid", "s1_researcher_background", "s1_researcher_goal"]
        for field in required_fields:
            assert field in entries[0], f"Entry should contain '{field}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
