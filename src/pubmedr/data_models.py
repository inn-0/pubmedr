# ./pubmedr/data_models.py
# useful pubmed docs = Query string documentation:   https://pubmed.ncbi.nlm.nih.gov/help/

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from pydantic.json_schema import SkipJsonSchema


class Settings(BaseModel):
    """Settings model that allows arbitrary field assignment."""

    model_config = ConfigDict(
        extra="allow",  # Allow arbitrary fields
        validate_assignment=False,  # Skip validation on assignment
        frozen=False,  # Allow mutation
    )

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get with default."""
        return getattr(self, key, default)


class S1Setup(BaseModel):
    s1_gsheet_id: SkipJsonSchema[str] = Field(..., title="Google Sheet ID")
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


class S2EnumTextAvailability(str, Enum):
    ALL = "all"
    ABSTRACT = "hasabstract"
    FREE_FULL_TEXT = "free full text[sb]"
    FULL_TEXT = "full text[sb]"


class S2EnumGender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    BOTH = "Both"


class S2EnumSpecies(str, Enum):
    HUMAN = "Humans"
    ANIMAL = "Other Animals"
    BOTH = "Both"


class S2EnumPublicationType(str, Enum):
    """Publication types relevant for toxicology research."""

    REVIEW = "Review[pt]"
    CLINICAL_TRIAL = "Clinical Trial[pt]"
    CLINICAL_TRIAL_PHASE_1 = "Clinical Trial, Phase I[pt]"
    CLINICAL_TRIAL_PHASE_2 = "Clinical Trial, Phase II[pt]"
    CLINICAL_TRIAL_PHASE_3 = "Clinical Trial, Phase III[pt]"
    CLINICAL_TRIAL_PHASE_4 = "Clinical Trial, Phase IV[pt]"
    CONTROLLED_CLINICAL_TRIAL = "Controlled Clinical Trial[pt]"
    EVALUATION_STUDY = "Evaluation Study[pt]"
    JOURNAL_ARTICLE = "Journal Article[pt]"
    META_ANALYSIS = "Meta-Analysis[pt]"
    MULTICENTER_STUDY = "Multicenter Study[pt]"
    OBSERVATIONAL_STUDY = "Observational Study[pt]"
    VALIDATION_STUDY = "Validation Study[pt]"
    RESEARCH_SUPPORT = "Research Support[pt]"


class S2EnumArticleType(str, Enum):
    """Article types focused on toxicology and drug development."""

    CLINICAL_TRIAL = "Clinical Trial[Filter]"
    COMPARATIVE_STUDY = "Comparative Study[Filter]"
    EVALUATION_STUDY = "Evaluation Study[Filter]"
    META_ANALYSIS = "Meta-Analysis[Filter]"
    MULTICENTER_STUDY = "Multicenter Study[Filter]"
    OBSERVATIONAL_STUDY = "Observational Study[Filter]"
    SYSTEMATIC_REVIEW = "Systematic Review[Filter]"
    VALIDATION_STUDY = "Validation Study[Filter]"


class S2SettingsSimple(BaseModel):
    """Simple parameters for the search."""

    keywords: str | None = Field(default=None, description="Keywords or phrases to search for.")
    authors: str | None = Field(default=None, description="Search for papers by a specific author.")
    start_year: int | None = Field(
        default=None,
        description="Start year for custom date range (inclusive).",
        ge=1950,
        le=datetime.now().year,
    )
    end_year: int | None = Field(
        default=None,
        description="End year for custom date range (inclusive).",
        ge=1950,
        le=datetime.now().year,
    )
    text_availability: S2EnumTextAvailability | None = Field(default=None, description="Which Text Contents are Available on PubMed")
    exclusions: str | None = Field(
        default=None,
        description="Terms, authors, journals, affiliations etc. to exclude from search by automatically inserting 'NOT'",
    )
    system_prompt: str | None = Field(
        default=None,
        description="How the AI should behave when generating queries",
    )
    n_queries_to_generate: SkipJsonSchema[int | None] = Field(
        default=10,
        description="Total number of queries to generate (max 30)",
        ge=1,
        le=30,
    )
    n_results_limit_per_query: SkipJsonSchema[int | None] = Field(default=15, description="Total number of results per query (max 50)", ge=1, le=50)

    @field_validator("start_year", "end_year")
    @classmethod
    def validate_years(cls, v: int | None, info: ValidationInfo) -> int | None:
        start_year = info.data.get("start_year")
        end_year = info.data.get("end_year")

        if v is None:
            return v

        if info.field_name == "end_year" and start_year is not None and v < start_year:
            raise ValueError("end_year must be greater than or equal to start_year")

        if info.field_name == "start_year" and end_year is not None and v > end_year:
            raise ValueError("start_year must be less than or equal to end_year")

        return v


class S2SettingsAdvanced(BaseModel):
    """Data model for Advanced Search Settings."""

    first_author: str | None = Field(default=None, description="Specify first author, intelligently inserts [1au]")
    last_author: str | None = Field(default=None, description="Specify last author, intelligently inserts [lastau]")
    substance_name: str | None = Field(default=None, description="Search for specific chemicals or drugs.")
    proximity_distance: int | None = Field(default=None, description="Word proximity distance for proximity search.", ge=0)
    species: S2EnumSpecies | None = Field(default=None, description="Limit to human or animal studies.")
    gender: S2EnumGender | None = Field(default=None, description="Specify male or female studies.")
    mesh_terms: str | None = Field(default=None, description="List of MeSH terms.")
    publication_types: list[S2EnumPublicationType] | None = Field(default_factory=list, description="Filter by publication types (e.g., Clinical Trial, Review).")
    unique_identifiers: str | None = Field(default=None, description="Search by unique identifiers (e.g., PMID, DOI).")
    affiliations: str | None = Field(default=None, description="Affiliations")
    article_types: list[S2EnumArticleType] | None = Field(default_factory=list, description="Specify article types (e.g., Meta-Analysis, Systematic Reviews).")


class S2Settings(S2SettingsSimple, S2SettingsAdvanced):
    """Combined data model for all Search Settings."""

    pass


class S2Query(BaseModel):
    """Core query model used throughout the application."""

    query_text: str = Field(
        default="",
        description="PubMed query string with proper syntax and formatting",
        examples=["Doktorova T AND (Triclosan[Substance Name] OR Triclosan[Title/Abstract])"],
    )
    uid: SkipJsonSchema[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        exclude=True,
    )
    is_selected: SkipJsonSchema[bool] = Field(
        default=False,
        exclude=True,
    )
    is_displayed: SkipJsonSchema[bool] = Field(
        default=True,
        exclude=True,
    )


class S2ChatInputBase(BaseModel):
    """Base class for chat inputs."""

    setup: S1Setup
    chat_input: str = Field(..., description="User question or instruction")


class S2ChatOutputBase(BaseModel):
    """Base output including queries."""

    queries: list[S2Query] = Field(
        default_factory=list,
        description="Generated PubMed queries with proper syntax",
    )


class S2AIJobInputSimple(S2ChatInputBase):
    current_settings: S2SettingsSimple


class S2AIJobInputAdvanced(S2ChatInputBase):
    current_settings: S2Settings


class S2AIJobOutputSimple(S2ChatOutputBase):
    updated_settings: S2SettingsSimple


class S2AIJobOutputAdvanced(S2ChatOutputBase):
    updated_settings: S2Settings


class S3AIJobInputSimple(BaseModel):
    search_settings: S2SettingsSimple
    recent_queries: list[str] = Field(..., description="Most recent round of queries.")
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S3AIJobInputAdvanced(BaseModel):
    search_settings: S2Settings
    recent_queries: list[str] = Field(..., description="Most recent round of queries.")
    chat_input: str = Field(..., description="User question, use this to adjust answers")


class S3AIJobOutput(BaseModel):
    """Output from AI query generation."""

    queries: list[S2Query] = Field(default_factory=list)


class S4Results(BaseModel):
    pmid: str = Field(..., description="PubMed ID of the article")
    title: str = Field(..., description="Article title")
    authors: list[str] = Field(default_factory=list, description="List of all authors")
    first_author: str = Field("", description="First author of the article")
    last_author: str | None = Field(None, description="Last author of the article")
    abstract: str | None = Field(None, description="Article abstract")
    journal: str = Field("", description="Journal name")
    pub_date: datetime | None = Field(None, description="Publication date")
    doi: str | None = Field(None, description="Digital Object Identifier")
    keywords: list[str] = Field(default_factory=list, description="Author keywords")
    mesh_terms: list[str] = Field(default_factory=list, description="MeSH terms")
    publication_types: list[str] = Field(default_factory=list, description="Publication types")
    is_free: bool = Field(False, description="Whether article has free full text")
    affiliations: list[str] = Field(default_factory=list, description="Author affiliations")

    @classmethod
    def from_metapub_article(cls, article) -> "S4Results":
        authors = getattr(article, "authors", [])
        pub_date = None
        if hasattr(article, "year"):
            try:
                pub_date = datetime.strptime(article.year, "%Y")
            except ValueError:
                pass

        # Convert publication_types from dict to list if it exists
        pub_types = []
        if hasattr(article, "publication_types"):
            pub_types = list(article.publication_types.values())

        return cls(
            pmid=article.pmid,
            title=getattr(article, "title", ""),
            authors=authors,
            first_author=authors[0] if authors else "",
            last_author=authors[-1] if len(authors) > 1 else None,
            abstract=getattr(article, "abstract", None),
            journal=getattr(article, "journal", ""),
            pub_date=pub_date,
            doi=getattr(article, "doi", None),
            keywords=getattr(article, "keywords", []),
            mesh_terms=getattr(article, "mesh_terms", []),
            publication_types=pub_types,  # Use the converted list
            is_free=bool(getattr(article, "pmc", None)),
            affiliations=getattr(article, "affiliations", []),
        )


class S4QuestionAnswer(BaseModel):
    question: SkipJsonSchema[str | None] = Field(default=None)
    answer: str | None = Field(
        default=None,
        description="Brief 1-2 sentence summary highlighting key relevance for the researcher",
    )


class S5AIJobInput(BaseModel):
    content: str = Field(..., description="Contents from the dataframe as a single string.")


class S5AIJobOutput(BaseModel):
    answer: str = Field(..., description="Answer generated by the AI.")


class S5StateSnapshot(BaseModel):
    """Complete state snapshot for restoration."""

    s0_is_advanced_mode: bool
    s1_setup: S1Setup
    s2_settings: S2SettingsSimple | S2Settings
    s2_query: S2Query | None = None  # Single query that led to this result
    s3_editor_states: dict[str, str] = Field(default_factory=dict)  # uid -> editor content
    s4_result: S4Results | None = None  # Single result being saved


class S5SavedResult(BaseModel):
    """Individual saved result with metadata."""

    # State snapshot (for restoration)
    s5_state: S5StateSnapshot
    s5_state_raw: str = Field(
        description="JSON serialized state for direct DB storage",
        exclude=True,
    )

    # Human readable fields (for sheet display)
    s5_paper_metadata: S4Results
    s5_user_note: str
    s5_search_context: dict[str, Any] = Field(
        description="Search settings that led to this result",
        default_factory=lambda: {
            "query_text": "",
            "results_count": 0,
            "researcher_goal": "",
            "keywords": "",
        },
    )

    def to_sheet_row(self) -> dict[str, str]:
        """Convert to flattened dict for sheet storage."""
        return {
            # Paper details
            "s4_paper_title": self.s5_paper_metadata.title,
            "s4_paper_authors": ", ".join(self.s5_paper_metadata.authors),
            "s4_paper_year": str(self.s5_paper_metadata.pub_date.year) if self.s5_paper_metadata.pub_date else "",
            "s4_paper_journal": self.s5_paper_metadata.journal,
            "s4_paper_abstract": self.s5_paper_metadata.abstract or "",
            "s4_paper_pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{self.s5_paper_metadata.pmid}/",
            # Research context
            "s1_researcher_goal": self.s5_search_context["researcher_goal"],
            "s3_search_query": self.s5_search_context["query_text"],
            "s5_user_note": self.s5_user_note,
            # State snapshot for restoration
            "s5_state_snapshot": self.s5_state_raw,
            # Metadata
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    def from_current_state(
        cls,
        result: S4Results,
        note: str,
        query: str,
        results_count: int,
        settings: dict[str, Any],
        setup: dict[str, Any],
        editor_states: dict[str, str],
        is_advanced: bool,
    ) -> "S5SavedResult":
        """Create from current UI state."""
        # Convert setup dict to S1Setup
        setup_model = S1Setup(
            s1_gsheet_id=setup.get("s1_gsheet_id", ""),
            s1_researcher_background=setup.get("s1_researcher_background", ""),
            s1_researcher_goal=setup.get("s1_researcher_goal", ""),
        )

        # Convert settings dict to appropriate settings model
        settings_cls = S2Settings if is_advanced else S2SettingsSimple
        settings_model = settings_cls(**settings)

        state = S5StateSnapshot(
            s0_is_advanced_mode=is_advanced,
            s1_setup=setup_model,
            s2_settings=settings_model,
            s2_query=S2Query(query_text=query),
            s3_editor_states=editor_states,
        )

        return cls(
            s5_state=state,
            s5_state_raw=state.model_dump_json(),
            s5_paper_metadata=result,
            s5_user_note=note,
            s5_search_context={
                "query_text": query,
                "results_count": results_count,
                "researcher_goal": setup_model.s1_researcher_goal,
                "keywords": settings_model.keywords or "",
            },
        )

    @classmethod
    def from_staged_state(
        cls,
        result: S4Results,
        note: str,
        query: S2Query,
        results_count: int,
        state: S5StateSnapshot,
    ) -> "S5SavedResult":
        """Create from pre-staged state snapshot."""
        return cls(
            s5_state=state,
            s5_state_raw=state.model_dump_json(),
            s5_paper_metadata=result,
            s5_user_note=note,
            s5_search_context={
                "query_text": query.query_text,
                "results_count": results_count,
                "researcher_goal": state.s1_setup.s1_researcher_goal,
                "keywords": state.s2_settings.keywords or "",
            },
        )


class S5ChatInput(BaseModel):
    content: str = Field(..., description="Content to analyze")


class S5ChatOutput(BaseModel):
    answer: str = Field(..., description="Generated answer")
