# ./pubmedr/streamlit_main.py

from datetime import datetime
from pathlib import Path

import streamlit as st

from pubmedr import config
from pubmedr.constants import MOCK_DATA
from pubmedr.data_models import S2Query, Settings
from pubmedr.streamlit_components import (
    S0_SidebarSettings,
    S1_ResearcherSetup,
    S2_Advanced,
    S2_PubmedSearchSettings,
    S3_CodeEditor,
    S4_Results,
    S5_SavedPapers,
)
from pubmedr.streamlit_utils import (
    s0_load_settings,
    s0_save_settings,
    s2_prase_chat,
    s3_handle_chat_input,
    s3_run_selected_queries,
    s3_update_query_contents,
    s4_note_tools,
    s5_load_results_df,
    s5_process_chat,
    s5_restore_state,
)

logger = config.custom_logger(__name__)


def s0_init_session_state():
    """Initialize session state variables."""
    if "is_advanced" not in st.session_state:
        st.session_state.is_advanced = False
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "queries" not in st.session_state:
        st.session_state.queries = [S2Query()]
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "settings" not in st.session_state:
        st.session_state.settings = Settings()


def s0_display_sidebar():
    """Display and handle sidebar settings."""
    with st.sidebar:
        with st.popover("View Readme"):
            readme_text = (Path(__file__).parent.parent.parent / "README.md").read_text()
            st.markdown(readme_text)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load Most Recent", type="secondary", disabled=config.LOCK_GSHEET):
                s0_load_settings()
        with col2:
            if st.button("Save Current Settings", type="primary", disabled=config.LOCK_GSHEET):
                s0_save_settings()

        st.markdown(
            f"[Open Google Sheet (Persistent Database)](https://docs.google.com/spreadsheets/d/{MOCK_DATA['setup']['gsheet_id']}) - Public Load/Save is Disabled for Security",
        )

        is_advanced = S0_SidebarSettings.search_settings()
        st.session_state.is_advanced = is_advanced

        operation = S0_SidebarSettings.chat_operation()
        st.session_state.chat_mode = operation
        s0_display_chat_history()

        s0_handle_chat_input(operation)


def s0_display_chat_history():
    """Display all chat messages."""
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def s0_handle_chat_input(operation: str):
    """Handle chat input based on operation mode."""
    chat_input = st.chat_input("Give instructions or ask questions...")
    if not chat_input:
        return

    try:
        if operation == "settings":
            s2_prase_chat(chat_input)
        elif operation == "queries":
            s3_handle_chat_input(chat_input)
        elif operation == "papers":
            df = s5_load_results_df()
            s5_process_chat(chat_input, df)
    except Exception as e:
        st.error(f"Failed to process chat: {str(e)}")
        logger.error("Chat processing error", exc_info=True)


def s1_display_researcher_setup():
    """Display researcher setup section."""
    st.header("1. Researcher Setup")
    with st.container(border=True, key="researcher_setup"):
        col1, col2 = st.columns(2)
        with col1:
            S1_ResearcherSetup.background()
        with col2:
            S1_ResearcherSetup.goal()


def s2_display_search_settings(is_advanced: bool):
    """Display and handle search settings."""
    st.header("2. Pubmed Search Settings")
    with st.container(border=True, key="pubmed_search_settings"):
        settings = st.session_state.get("settings", Settings())
        if isinstance(settings, dict):
            settings = Settings(**settings)

        # Basic settings section
        with st.container():
            if keywords := S2_PubmedSearchSettings.keywords(settings):
                setattr(settings, "keywords", keywords)
            if years := S2_PubmedSearchSettings.year_range(settings):
                setattr(settings, "start_year", years[0])
                setattr(settings, "end_year", years[1])

            col1, col2 = st.columns(2)
            with col1:
                if authors := S2_PubmedSearchSettings.authors(settings):
                    setattr(settings, "authors", authors)
            with col2:
                if exclusions := S2_PubmedSearchSettings.exclusions(settings):
                    setattr(settings, "exclusions", exclusions)

            col1, _, col2, _, col3 = st.columns([44, 6, 22, 6, 22])
            with col1:
                if text_avail := S2_PubmedSearchSettings.text_availability(settings):
                    setattr(settings, "text_availability", text_avail)
            with col2:
                if query_count := S2_PubmedSearchSettings.query_count(settings):
                    setattr(settings, "n_queries_to_generate", query_count)
            with col3:
                if results_per_query := S2_PubmedSearchSettings.results_per_query(settings):
                    S2_PubmedSearchSettings._update_settings(settings, "results_per_query", results_per_query)

        # Advanced settings
        if is_advanced:
            with st.expander("Advanced Settings", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    if pub_types := S2_Advanced.pub_types(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "publication_types", [f"{pt}[pt]" for pt in pub_types])
                with col2:
                    if article_types := S2_Advanced.article_types(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "article_types", [f"{at}[Filter]" for at in article_types])

                col1, col2 = st.columns(2)
                with col1:
                    if first_author := S2_Advanced.first_author(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "first_author", first_author)
                with col2:
                    if last_author := S2_Advanced.last_author(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "last_author", last_author)

                col1, _, col2, _, col3 = st.columns([33, 6, 33, 6, 22])
                with col1:
                    if species := S2_Advanced.species(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "species", species)
                with col2:
                    if gender := S2_Advanced.gender(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "gender", gender)
                with col3:
                    if proximity := S2_Advanced.proximity(is_advanced, settings):
                        S2_PubmedSearchSettings._update_settings(settings, "proximity", proximity)

                # Additional filters
                for row_fields in [
                    ("affiliations", "identifiers"),
                    ("substance", "mesh_terms"),
                ]:
                    col1, col2 = st.columns(2)
                    for i, field in enumerate([col1, col2]):
                        with field:
                            if value := getattr(S2_Advanced, row_fields[i])(is_advanced, settings):
                                setattr(settings, row_fields[i], value)

        # Always update session state after any changes
        st.session_state.settings = settings


def s3_display_query_management():
    """Display the query management section."""
    st.header("3. Query Management")
    with st.container(border=True, key="query_management"):
        displayed_queries = [q for q in st.session_state.queries if q.is_displayed]

        for query in displayed_queries:
            with st.container():
                col1, col2 = st.columns([95, 5])
                with col1:
                    response = S3_CodeEditor.editor_config(query, key=f"editor_{query.uid}")
                    if response["type"] == "submit":
                        s3_update_query_contents()
                with col2:
                    was_selected = query.is_selected
                    is_selected = st.checkbox(
                        "Select query for processing",
                        value=query.is_selected,
                        key=f"select_{query.uid}",
                        label_visibility="collapsed",
                    )
                    full_idx = next(i for i, sq in enumerate(st.session_state.queries) if sq.uid == query.uid)
                    st.session_state.queries[full_idx].is_selected = is_selected
                    if was_selected != is_selected:
                        st.rerun()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        status_container = st.container()

        st.markdown(
            "If you edit a text box you must manually save before updates take effect. "
            "Start typing to discover custom pubmed [hotkeys](https://pubmed.ncbi.nlm.nih.gov/help/#search-pubmed)! "
            "A good strategy is making many small terms, then successively joining them with AND to narrow-down into domains.",
        )

        with col1:
            if st.button("Add New Field", type="secondary"):
                st.session_state.queries.append(S2Query(query_text=""))
                st.rerun()
        with col2:
            if st.button("Select All/None", type="secondary"):
                all_selected = all(q.is_selected for q in displayed_queries)
                for q in st.session_state.queries:
                    if q.is_displayed:
                        q.is_selected = not all_selected
                st.rerun()
        with col3:
            if st.button("Delete Selected", type="secondary"):
                for q in st.session_state.queries:
                    if q.is_selected and q.is_displayed:
                        q.is_displayed = False
                        q.is_selected = False
                st.rerun()
        with col4:
            if st.button("Run Individually", type="primary"):
                s3_run_selected_queries(status_container)
        with col5:
            if st.button("Run Merged (OR)", type="primary"):
                s3_run_selected_queries(status_container, "OR")
        with col6:
            if st.button("Run Merged (AND)", type="primary"):
                s3_run_selected_queries(status_container, "AND")


def s4_display_search_results():
    """Display search results section."""
    st.header("4. Search Results")
    with st.container(border=True, key="search_results"):
        if "search_results" in st.session_state:
            for group_idx, result_group in enumerate(st.session_state.search_results):
                timestamp = datetime.fromisoformat(result_group["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                with st.expander(
                    f"{len(result_group['results'])} Results  —  {timestamp}\n{result_group['query']}",
                    expanded=True,
                ):
                    for idx, result in enumerate(result_group["results"]):
                        with st.container(border=True):
                            col1, col2 = st.columns([30, 70])
                            with col1:
                                # Use component for research notes
                                note_key = f"note_group{group_idx}_{result_group['timestamp']}_{idx}"
                                S4_Results.research_notes(note_key)
                                s4_note_tools(
                                    note_key=note_key,
                                    result=result,
                                    query=result_group["query"],
                                    group_idx=group_idx,
                                )

                            with col2:
                                st.markdown(f"**Title**: {result.title}")
                                year = result.pub_date.year if result.pub_date else "N/A"
                                st.markdown(f"**Year**: {year}   **Journal**: {result.journal}")
                                st.markdown(f"**Authors**: {', '.join(result.authors)}")
                                st.markdown(f"[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{result.pmid}/)")

                                with st.container(height=200):
                                    if result.abstract:
                                        st.markdown(f"**Abstract**: {result.abstract}")
                                    else:
                                        st.warning("No abstract available")


def s5_display_saved_papers():
    """Display the saved papers section."""
    st.header("5. Saved Papers")
    with st.container(border=True, key="saved_papers"):
        # Load the dataframe
        df = s5_load_results_df()
        S5_SavedPapers.display_dataframe(df, s5_restore_state)


def main():
    """Main Streamlit application."""
    st.set_page_config(layout="wide", page_icon="./assets/InnoSwit.ch_icon_square.ico")
    st.title("PubMedR - PubMed Researcher Assistant UI")

    s0_init_session_state()
    s0_display_sidebar()
    s1_display_researcher_setup()
    s2_display_search_settings(st.session_state.is_advanced)
    s3_display_query_management()
    s4_display_search_results()
    s5_display_saved_papers()


if __name__ == "__main__":
    main()
