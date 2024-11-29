# ./pubmedr/streamlit_components.py

# The basic problem is that Streamlit can't update the value of a widget that has
# already been created. So we need to create a new widget with a unique key each time we
# update the value, then assign the new value to the current Streamlit widget.
# Otherwise Streamlit can only update 'input' areas via direct input,
# not programmatically.

from datetime import datetime
from typing import Any, Callable, TypeVar

import pandas as pd
import streamlit as st
from code_editor import code_editor

from pubmedr import config
from pubmedr.constants import INFO_BAR, INFO_BAR_BUTTONS, PUBMED_COMPLETIONS
from pubmedr.data_models import (
    S2EnumArticleType,
    S2EnumGender,
    S2EnumPublicationType,
    S2EnumSpecies,
    S2EnumTextAvailability,
    S2Query,
    Settings,
)


class StreamlitComponent:
    """Base class for Streamlit components with common functionality."""

    @staticmethod
    def _get_stored_value(key: str, settings: Settings | None = None, default: Any = None) -> Any:
        """Get value from session state storage or settings."""
        storage_key = f"{key}_storage"
        if storage_key in st.session_state:
            return st.session_state[storage_key]
        if settings is not None:
            return settings.get(key, default)
        return default

    @staticmethod
    def _update_settings(settings: Settings, key: str, value: Any):
        """Update settings dict if value is not None."""
        if value is not None:
            setattr(settings, key, value)

    @staticmethod
    def _handle_widget_state(
        key: str,
        settings: Settings | None = None,
        default: Any = None,
        transform_initial: Callable[[Any], Any] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Handle widget state management.

        Args:
            key: Base key for the widget
            settings: Settings object to get initial value from
            default: Default value if not found in settings
            transform_initial: Optional function to transform initial value

        Returns:
            Tuple of (initial_value, widget_args_dict)
        """
        storage_key = f"{key}_storage"
        widget_key = f"{key}_widget"

        if storage_key in st.session_state:
            initial_value = st.session_state[storage_key]
        elif settings is not None:
            initial_value = settings.get(key, default)
        else:
            initial_value = default

        if transform_initial and initial_value is not None:
            initial_value = transform_initial(initial_value)

        def on_change() -> None:
            st.session_state[storage_key] = st.session_state[widget_key]

        widget_args = {"key": widget_key, "on_change": on_change}
        return initial_value, widget_args


class S0_SidebarSettings(StreamlitComponent):
    @staticmethod
    def search_settings() -> bool:
        """Control search settings complexity."""
        return (
            st.radio(
                "Search Settings",
                ["Simple Settings", "Advanced Settings"],
                help="Select 'Advanced Settings' to enable extra features",
                horizontal=True,
            )
            == "Advanced Settings"
        )

    @staticmethod
    def chat_operation() -> str:
        """Control chat operation mode."""
        operation = st.radio(
            "Chat Operation",
            [
                "A. Refine Settings (also makes queries)",
                "B. Refine Queries (no change to settings)",
                "C. Get Answers (only uses saved papers)",
            ],
            help="Each chat takes in all current content from sections 1. (Researcher Setup) "
            "2. (Pubmed Search Settings) 3. (Generated Pubmed Queries), and the entire chat history. "
            "Use Chat Operation A. to tweak your filter settings, use Chat Operation B. to generate "
            "query variations, use Chat Operation C. to get quick answers from saved papers.",
        )
        operation_map = {
            "A. Refine Settings (also makes queries)": "settings",
            "B. Refine Queries (no change to settings)": "queries",
            "C. Get Answers (only uses saved papers)": "papers",
        }
        return operation_map[operation]


class S1_ResearcherSetup(StreamlitComponent):
    @staticmethod
    def background() -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("researcher_background", default="")
        return st.text_area(
            "Researcher Background",
            value=initial_value,
            height=230,
            help="General info about your overall role and expertise",
            placeholder="e.g. Toxicology researcher specialised in in-vivo and in-silico modelling",
            **widget_args,
        )

    @staticmethod
    def goal() -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("researcher_goal", default="")
        return st.text_area(
            "Research Goal",
            value=initial_value,
            height=230,
            help="Your current research goal or objective, note it here to help you keep track of your research questions or working hypotheses as they evolve - feel free to paste in long context or rough research notes, these are saved with the resultant papers to pre-answer your likely questions",
            placeholder="e.g. Investigating Triclosan effects in hepatic models, currently thinking to find...",
            **widget_args,
        )


class S2_PubmedSearchSettings(StreamlitComponent):
    T = TypeVar("T", Settings, dict[str, Any])

    @staticmethod
    def _to_dict(settings: T) -> dict[str, Any]:
        """Convert settings to dict, handling both Pydantic and dict inputs."""
        if isinstance(settings, dict):
            return settings
        if isinstance(settings, Settings):
            return settings.model_dump()
        return {}

    @staticmethod
    def update_settings(settings: T | None = None):
        """Update settings in session state from UI components."""
        if settings is None:
            return
        st.session_state.settings = S2_PubmedSearchSettings._to_dict(settings)

    @staticmethod
    def keywords(settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("keywords", settings)
        return st.text_area(
            "Keywords",
            value=initial_value,
            help="Main search terms, combined with AND by default",
            height=68,
            **widget_args,
        )

    @staticmethod
    def year_range(settings: Settings | None = None) -> tuple[int, int] | None:
        """Year range slider for publication dates."""
        current_year = datetime.now().year
        storage_key = "year_range_storage"
        widget_key = "year_range_widget"

        # Get initial values
        if storage_key in st.session_state:
            start_year, end_year = st.session_state[storage_key]
        elif settings:
            # Handle None values with defaults
            start_year = settings.get("start_year")
            end_year = settings.get("end_year")

            # Use defaults if None
            start_year = int(start_year) if start_year is not None else current_year - 14
            end_year = int(end_year) if end_year is not None else current_year
        else:
            start_year = current_year - 14
            end_year = current_year

        def on_change() -> None:
            st.session_state[storage_key] = st.session_state[widget_key]

        years = st.slider(
            "Publication Years",
            min_value=1950,
            max_value=current_year,
            value=(start_year, end_year),
            key=widget_key,
            on_change=on_change,
            help="Select publication year range",
        )

        # Only return if values changed from initial
        if years != (start_year, end_year):
            return years
        return None

    @staticmethod
    def authors(settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("authors", settings)
        return st.text_input(
            "Authors",
            value=initial_value,
            help="Specific authors to include",
            placeholder="e.g. Doktorova TY",
            **widget_args,
        )

    @staticmethod
    def exclusions(settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("exclusions", settings)
        return st.text_input(
            "Exclusions",
            value=initial_value,
            help="Terms to exclude (combined with NOT)",
            placeholder="e.g. USA, meta-analysis",
            **widget_args,
        )

    @staticmethod
    def text_availability(settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "text_availability",
            settings,
            default=S2EnumTextAvailability.ABSTRACT.value,
        )
        return st.radio(
            "Text Availability",
            options=[e.value for e in S2EnumTextAvailability],
            index=None if initial_value is None else [e.value for e in S2EnumTextAvailability].index(initial_value),
            horizontal=True,
            **widget_args,
        )

    @staticmethod
    def system_prompt(settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "system_prompt",
            settings,
            default="Make a mixture of very short queries, and a few longer combined ones. If filter settings are already set try to preserve them unless they contradict new instructions.",
        )
        return st.text_area(
            "System Prompt",
            value=initial_value,
            help="Specify how you want the AI to behave",
            height=68,
            placeholder="Instructions for query generation...",
            label_visibility="visible",
            disabled=False,
            **widget_args,
        )

    @staticmethod
    def query_count(settings: Settings | None = None) -> int | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "n_queries_to_generate",
            settings,
            default=10,
        )
        return st.number_input(
            "Number of Queries",
            min_value=1,
            max_value=30,
            value=initial_value,
            step=1,
            help="Total number of queries to generate (max 30)",
            label_visibility="visible",
            disabled=False,
            **widget_args,
        )

    @staticmethod
    def results_per_query(settings: Settings | None = None) -> int | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "n_results_limit_per_query",
            settings,
            default=15,
        )
        return st.number_input(
            "Results Per Query",
            min_value=1,
            max_value=50,
            value=initial_value,
            step=1,
            help="Total number of results to return for a given pubmed query (max 50)",
            label_visibility="visible",
            disabled=False,
            **widget_args,
        )


class S2_Advanced(StreamlitComponent):
    @staticmethod
    def first_author(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("first_author", settings)
        return st.text_input(
            "First Author",
            value=initial_value,
            help="Specify first author, intelligently inserts [1au]",
            placeholder="e.g. Doktorova TY",
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def last_author(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("last_author", settings)
        return st.text_input(
            "Last Author",
            value=initial_value,
            help="Specify last author, intelligently inserts [lastau]",
            placeholder="e.g. Rogiers V",
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def pub_types(is_advanced: bool, settings: Settings | None = None) -> list[str] | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "publication_types",
            settings,
            default=[],
            transform_initial=lambda x: [pt.replace("[pt]", "") for pt in x] if x else [],
        )
        return st.multiselect(
            "Publication Types",
            options=[e.value.replace("[pt]", "") for e in S2EnumPublicationType],
            default=initial_value,
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def article_types(is_advanced: bool, settings: Settings | None = None) -> list[str] | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "article_types",
            settings,
            default=[],
            transform_initial=lambda x: [at.replace("[Filter]", "") for at in x] if x else [],
        )
        return st.multiselect(
            "Article Types",
            options=[e.value.replace("[Filter]", "") for e in S2EnumArticleType],
            default=initial_value,
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def species(is_advanced: bool, settings: Settings | None = None) -> str:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "species",
            settings,
            default=S2EnumSpecies.BOTH.value,
        )
        return st.radio(
            "Species",
            options=[e.value for e in S2EnumSpecies],
            index=[e.value for e in S2EnumSpecies].index(initial_value),
            horizontal=True,
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def gender(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state(
            "gender",
            settings,
            default=S2EnumGender.BOTH.value,
        )
        return st.radio(
            "Gender",
            options=[e.value for e in S2EnumGender],
            index=None if initial_value is None else [e.value for e in S2EnumGender].index(initial_value),
            horizontal=True,
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def proximity(is_advanced: bool, settings: Settings | None = None) -> int | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("proximity", settings)
        return st.number_input(
            "Proximity Distance",
            min_value=0,
            max_value=200,
            value=initial_value,
            help=(
                'Word proximity distance for proximity search (leave empty to disable). Example: "liver toxicity"[Title/Abstract:~10] '
                "finds these words within 10 words of each other, looking only in the e.g. Title and Abstract."
            ),
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def identifiers(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("identifiers", settings)
        return st.text_input(
            "Unique Identifiers",
            value=initial_value,
            help="Search by PMID or DOI",
            placeholder="e.g. PMCID=30196099, DOI=10.1016/j.tiv.2018.09.002",
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def affiliations(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("affiliations", settings)
        return st.text_input(
            "Affiliations",
            value=initial_value,
            help="Search by institution or organization affiliations",
            placeholder="e.g. Vrije Universiteit Brussel",
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def substance(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("substance", settings)
        return st.text_input(
            "Specific Substance Name",
            value=initial_value,
            help="Search for specific chemicals or drugs",
            placeholder="e.g. Triclosan, Piperonyl Butoxide",
            disabled=not is_advanced,
            **widget_args,
        )

    @staticmethod
    def mesh_terms(is_advanced: bool, settings: Settings | None = None) -> str | None:
        initial_value, widget_args = StreamlitComponent._handle_widget_state("mesh_terms", settings)
        return st.text_input(
            "Specific MeSH Terms",
            value=initial_value,
            help="Medical Subject Headings terms to include",
            placeholder="e.g. Drug Toxicity, Liver Diseases",
            disabled=not is_advanced,
        )


class S3_CodeEditor:
    @staticmethod
    @st.cache_resource
    def _get_editor_config() -> dict:
        """Get the static configuration for the code editor."""
        return {
            "lang": "sql",
            "height": 100,
            "theme": "default",
            "shortcuts": "sublime",
            "buttons": INFO_BAR_BUTTONS,
            "info": INFO_BAR,
            "options": {
                "wrap": True,
                "fontSize": 14,
                "enableBasicAutocompletion": True,
                "enableLiveAutocompletion": True,
                "showGutter": False,
                "highlightActiveLine": True,
                "showPrintMargin": False,
            },
            "completions": PUBMED_COMPLETIONS,
        }

    @staticmethod
    def editor_config(query: S2Query, key: str) -> dict[str, Any]:
        """Get the editor configuration with query-specific settings."""
        config = S3_CodeEditor._get_editor_config()
        return code_editor(query.query_text, key=key, **config)


class S4_Results(StreamlitComponent):
    @staticmethod
    def research_notes(note_key: str) -> str | None:
        """Display research notes text area with any stored content."""
        initial_value, widget_args = StreamlitComponent._handle_widget_state(note_key, default="")
        return st.text_area(
            "Research Notes",
            value=initial_value,
            height=250,
            placeholder="Add any notes or thoughts here before you save.",
            label_visibility="collapsed",
            **widget_args,
        )


class S5_SavedPapers:
    @staticmethod
    @st.cache_resource
    def _get_column_config() -> dict:
        """Get the static column configuration for the data editor."""
        return {
            "Selected": st.column_config.CheckboxColumn(
                label="Selected",
                disabled=False,
                default=False,
                width="small",
            ),
            "s1_researcher_goal": st.column_config.TextColumn("Research Goal", width=None, disabled=True),
            "s5_user_note": st.column_config.TextColumn("Notes", width="medium", disabled=True),
            "s4_paper_title": st.column_config.TextColumn("Title", width=None, disabled=True),
            "s4_paper_pubmed_url": st.column_config.LinkColumn("PubMed Link", width=None, disabled=True),
            "s4_paper_authors": st.column_config.TextColumn("Authors", width="medium", disabled=True),
            "s4_paper_year": st.column_config.NumberColumn("Year", width=None, format="%d", disabled=True),
            "s4_paper_journal": st.column_config.TextColumn("Journal", width="medium", disabled=True),
            "s3_search_query": st.column_config.TextColumn("Search Query", width="medium", disabled=True),
            "s2_keywords": st.column_config.TextColumn("Keywords", width="medium", disabled=True),
            "s1_researcher_background": st.column_config.TextColumn("Research Background", width="medium", disabled=True),
            "timestamp": st.column_config.DatetimeColumn("Saved On", width="small", disabled=True),
            "s5_state_snapshot": st.column_config.TextColumn("State Snapshot", width="small", disabled=True),
        }

    @staticmethod
    @st.cache_data(ttl=120)
    def filter_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Filter and order columns for display."""
        display_columns = [
            "s1_researcher_goal",
            "s5_user_note",
            "s4_paper_title",
            "s4_paper_pubmed_url",
            "s4_paper_authors",
            "s4_paper_year",
            "s4_paper_journal",
            "s3_search_query",
            "s2_keywords",
            "s1_researcher_background",
            "timestamp",
            "s5_state_snapshot",  # Hidden but needed for state restoration
        ]
        # Ensure we return a DataFrame by using .loc for column selection
        return df.loc[:, [col for col in display_columns if col in df.columns]].copy()

    @staticmethod
    def display_dataframe(df: pd.DataFrame, on_restore_callback: Callable) -> None:
        if df.empty:
            st.info("No papers saved yet. Use the save buttons in the Search Results section to save papers.")
            return

        # Convert DataFrame to use Python native types
        df = df.astype({col: "object" for col in df.select_dtypes(include=["bool_"]).columns})
        df = df.copy()
        df.insert(0, "Selected", pd.Series([False] * len(df), dtype=bool))

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            column_config=S5_SavedPapers._get_column_config(),
            hide_index=True,
            disabled=False,
        )

        selected_rows = edited_df[edited_df["Selected"].astype(bool)].index
        if len(selected_rows) > 0:
            if st.button("Restore search settings from selected paper", type="primary", disabled=config.LOCK_GSHEET):
                on_restore_callback(selected_rows[0])
