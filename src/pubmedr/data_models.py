# data_models.py

from enum import Enum

import pandas as pd
from pydantic import BaseModel, Field, ValidationInfo, field_validator


class S1datamodelSetup(BaseModel):
    s1_gsheet_id: str = Field(..., title="Google Sheet ID")
    s1_researcher_background: str = Field(..., title="Researcher Background")
    s1_researcher_goal: str = Field(..., title="Specific Research Goal")

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the model to a pandas DataFrame."""
        # Try model_dump() first, fall back to dict() if needed
        try:
            return pd.DataFrame([self.model_dump()])
        except AttributeError:
            # Fallback for older Pydantic versions
            return pd.DataFrame([dict(self)])

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        """Create a model instance from a pandas DataFrame."""
        data = df.to_dict(orient="records")[0]  # Assuming one record
        return cls(**data)


class EnumDateRange(str, Enum):
    LAST_1_YEAR = "last 1 year"
    LAST_5_YEARS = "last 5 years"
    LAST_10_YEARS = "last 10 years"
    CUSTOM = "custom"


class EnumTextAvailability(str, Enum):
    ALL = "all"
    ABSTRACT = "hasabstract"
    FREE_FULL_TEXT = "free full text[sb]"
    FULL_TEXT = "full text[sb]"


class EnumGender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    BOTH = "Both"


class EnumSpecies(str, Enum):
    HUMAN = "Humans"
    ANIMAL = "Other Animals"
    BOTH = "Both"


# These were made by summarising the Query string documentation https://pubmed.ncbi.nlm.nih.gov/help/


class S2datamodelSettingsSimple(BaseModel):
    """Simple parameters for the search."""

    keywords: str | None = Field(None, description="Keywords or phrases to search for.")
    author: str | None = Field(None, description="Search for papers by a specific author.")
    date_range: EnumDateRange | None = Field(None, description="Date range for the search.")
    start_year: int | None = Field(
        None,
        description="Start year for custom date range (inclusive).",
        ge=1750,
        le=2026,
    )
    end_year: int | None = Field(
        None,
        description="End year for custom date range (inclusive).",
        ge=1750,
        le=2026,
    )
    text_availability: EnumTextAvailability | None = Field(None, description="Text availability options.")
    exclusions: list[str] | None = Field(
        default_factory=list, description="List of terms, authors, or journals to exclude."
    )

    # Validators
    @field_validator("end_year")
    @classmethod
    def validate_end_year(cls, v: int | None, info: ValidationInfo) -> int | None:
        start_year = info.data.get("start_year")
        if v is not None and start_year is not None:
            if v < start_year:
                raise ValueError("end_year must be greater than or equal to start_year")
        return v

    @field_validator("start_year", "end_year")
    @classmethod
    def validate_custom_date_range(cls, v: int | None, info: ValidationInfo) -> int | None:
        date_range = info.data.get("date_range")
        if date_range == EnumDateRange.CUSTOM:
            if v is None:
                field_name = info.field_name
                raise ValueError(f'{field_name} is required when date_range is "custom"')
        return v


class S2datamodelSettingsAdvanced(BaseModel):
    """Data model for Advanced Search Settings."""

    complex_boolean: bool | None = Field(False, description="Enable complex boolean logic.")
    first_author: str | None = Field(None, description="Specify first author.")
    last_author: str | None = Field(None, description="Specify last author.")
    substance_name: str | None = Field(None, description="Search for specific chemicals or drugs.")
    proximity_search_enabled: bool | None = Field(False, description="Enable proximity search.")
    proximity_distance: int | None = Field(50, description="Word proximity distance for proximity search.", ge=0)
    species: EnumSpecies | None = Field(None, description="Limit to human or animal studies.")
    gender: EnumGender | None = Field(None, description="Specify male or female studies.")
    mesh_terms: list[str] | None = Field(default_factory=list, description="List of MeSH terms.")
    publication_types: list[str] | None = Field(
        default_factory=list, description="Filter by publication types (e.g., Clinical Trial, Review)."
    )
    unique_identifiers: list[str] | None = Field(
        default_factory=list, description="Search by unique identifiers (e.g., PMID, DOI)."
    )
    affiliation_includes: list[str] | None = Field(
        default_factory=list, description="Affiliations to include in the search."
    )
    affiliation_excludes: list[str] | None = Field(
        default_factory=list, description="Affiliations to exclude from the search."
    )
    article_types: list[str] | None = Field(
        default_factory=list, description="Specify article types (e.g., Meta-Analysis, Systematic Reviews)."
    )
    result_limit: int | None = Field(999, description="Total number of results across all queries.", ge=1)


class S2datamodelSettings(S2datamodelSettingsSimple, S2datamodelSettingsAdvanced):
    """Combined data model for all Search Settings."""

    pass


class S2AIJobInputSimple(BaseModel):
    current_settings: S2datamodelSettingsSimple
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S2AIJobOutputSimple(BaseModel):
    updated_settings: S2datamodelSettingsSimple


class S2AIJobInputAdvanced(BaseModel):
    current_settings: S2datamodelSettings
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S2AIJobOutputAdvanced(BaseModel):
    updated_settings: S2datamodelSettings


class S3AIJobInputSimple(BaseModel):
    search_settings: S2datamodelSettingsSimple
    recent_queries: list[str] = Field(..., description="Most recent round of queries.")
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S3AIJobInputAdvanced(BaseModel):
    search_settings: S2datamodelSettings
    recent_queries: list[str] = Field(..., description="Most recent round of queries.")
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S3AIJobOutput(BaseModel):
    new_queries: list[str] = Field(..., description="List of generated queries.")


class S3datamodelQueries(BaseModel):  # TODO
    s3_queries: list[str] | None = None
    s3_selected_queries: list[str] | None = None
    """
    This data model should include fields for:
    - List of generated queries
    - Selected queries for execution
    - Edited queries
    """


class S4datamodelResults(BaseModel):
    s4_articles: list[dict] | None = None
    s4_selected_articles: list[dict] | None = None
    """
    This data model should include fields for:
    - Articles retrieved from queries
    - Selected articles to save
    """


class S5datamodelSaved(BaseModel):  # TODO
    s5_saved_papers: list[dict] | None = None
    s5_notes: dict[str, str] | None = None
    """
    This data model should include fields for:
    - Saved papers from Google Sheets
    - Notes taken by the user on each paper
    """


class S5AIJobInput(BaseModel):
    content: str = Field(..., description="Contents from the dataframe as a single string.")


class S5AIJobOutput(BaseModel):
    answer: str = Field(..., description="Answer generated by the AI.")
