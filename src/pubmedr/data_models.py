# data_models.py

from pydantic import BaseModel, Field
import pandas as pd


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


class S2datamodelSettings(BaseModel):
    s2_keyword: str | None = None
    s2_author: str | None = None
    """
    This data model should include fields for:
    - Keywords for search
    - Author names
    - Date range
    - Text availability options
    - Advanced search parameters
    """


class S3datamodelQueries(BaseModel):
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


class S5datamodelSaved(BaseModel):
    s5_saved_papers: list[dict] | None = None
    s5_notes: dict[str, str] | None = None
    """
    This data model should include fields for:
    - Saved papers from Google Sheets
    - Notes taken by the user on each paper
    """
