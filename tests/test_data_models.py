# test_data_models.py

import pandas as pd
import pytest
from pydantic import ValidationError
from test_gdrive import SHEET_ID

from pubmedr.data_models import (
    EnumSpecies,
    S1datamodelSetup,
    S2datamodelSettings,
    S2datamodelSettingsAdvanced,
    S2datamodelSettingsSimple,
)


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


class TestS2SettingsSimple:
    class TestInitialization:
        @pytest.mark.parametrize(
            "data, target, expected",
            [
                (
                    {"keywords": "CRISPR", "author": "Zhang F", "date_range": "last 5 years"},
                    "keywords",
                    "CRISPR",
                ),
                (
                    {"date_range": "custom", "start_year": 2020, "end_year": 2024},
                    "end_year",
                    2024,
                ),
                (
                    {"text_availability": "hasabstract", "exclusions": ["review"]},
                    "exclusions",
                    ["review"],
                ),
            ],
        )
        def test_valid_init(self, data, target, expected):
            settings = S2datamodelSettingsSimple(**data)
            assert getattr(settings, target) == expected

        @pytest.mark.parametrize(
            "data, error_msg",
            [
                (
                    {"date_range": "custom", "start_year": None},
                    "start_year is required when date_range is",
                ),
                (
                    {"date_range": "custom", "start_year": 2024, "end_year": 2020},
                    "end_year must be greater than or equal to start_year",
                ),
                (
                    {"start_year": 1700},  # Below minimum year
                    "Input should be greater than or equal to 1750",
                ),
            ],
        )
        def test_invalid_init(self, data, error_msg):
            with pytest.raises(ValidationError) as exc_info:
                S2datamodelSettingsSimple(**data)
            assert error_msg in str(exc_info.value)


class TestS2SettingsAdvanced:
    class TestInitialization:
        @pytest.mark.parametrize(
            "data, target, expected",
            [
                (
                    {"species": "Humans", "gender": "Both", "result_limit": 500},
                    "result_limit",
                    500,
                ),
                (
                    {"mesh_terms": ["CRISPR", "Cancer"], "proximity_distance": 25},
                    "mesh_terms",
                    ["CRISPR", "Cancer"],
                ),
                (
                    {"complex_boolean": True, "first_author": "Zhang"},
                    "first_author",
                    "Zhang",
                ),
            ],
        )
        def test_valid_init(self, data, target, expected):
            settings = S2datamodelSettingsAdvanced(**data)
            assert getattr(settings, target) == expected

        @pytest.mark.parametrize(
            "data, error_msg",
            [
                (
                    {"proximity_distance": -1},
                    "Input should be greater than or equal to 0",
                ),
                (
                    {"result_limit": 0},
                    "Input should be greater than or equal to 1",
                ),
            ],
        )
        def test_invalid_init(self, data, error_msg):
            with pytest.raises(ValidationError) as exc_info:
                S2datamodelSettingsAdvanced(**data)
            assert error_msg in str(exc_info.value)


class TestS2SettingsCombined:
    def test_combined_model(self):
        """Test the combined model inherits and validates both simple and advanced settings."""
        data = {
            # Simple settings
            "keywords": "CRISPR cancer",
            "date_range": "custom",
            "start_year": 2020,
            "end_year": 2024,
            "text_availability": "hasabstract",
            # Advanced settings
            "species": "Humans",
            "gender": "Both",
            "mesh_terms": ["CRISPR", "Cancer"],
            "result_limit": 500,
        }

        settings = S2datamodelSettings(**data)

        # Test inheritance
        assert isinstance(settings, S2datamodelSettingsSimple)
        assert isinstance(settings, S2datamodelSettingsAdvanced)

        # Test field validation from both parent classes
        assert settings.keywords == "CRISPR cancer"
        assert settings.start_year == 2020
        assert settings.species == EnumSpecies.HUMAN
        assert settings.result_limit == 500

        # Test validation error propagation from both parent classes
        with pytest.raises(ValidationError) as exc_info:
            S2datamodelSettings(
                date_range="custom",
                start_year=2024,
                end_year=2020,  # Invalid: end < start
                result_limit=0,  # Invalid: must be >= 1
            )
        error_str = str(exc_info.value)
        assert "end_year must be greater than or equal to start_year" in error_str
        assert "Input should be greater than or equal to 1" in error_str
