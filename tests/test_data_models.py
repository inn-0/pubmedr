# test_data_models.py

import pandas as pd
import pytest
from test_gdrive import SHEET_ID
from pubmedr.data_models import S1datamodelSetup


@pytest.fixture
def dummy_setup_data():
    return {
        "s1_gsheet_id": SHEET_ID,
        "s1_researcher_background": "PhD in Molecular Biology",
        "s1_researcher_goal": "Find recent papers about CRISPR in cancer therapy",
    }


def test_s1_datamodel(dummy_setup_data):
    """Test S1datamodelSetup model creation, DataFrame conversion, and roundtrip."""

    # Test model creation from dictionary
    setup = S1datamodelSetup(**dummy_setup_data)
    assert setup.dict() == dummy_setup_data

    # Test conversion to DataFrame
    df = setup.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, len(dummy_setup_data))
    assert df.iloc[0].to_dict() == dummy_setup_data

    # Test creation from DataFrame
    setup_from_df = S1datamodelSetup.from_dataframe(df)
    assert setup_from_df == setup

    # Test model -> DataFrame -> model roundtrip
    setup_roundtrip = S1datamodelSetup.from_dataframe(setup.to_dataframe())
    assert setup_roundtrip == setup
