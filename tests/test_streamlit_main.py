import time
from datetime import datetime
from pathlib import Path

import logfire
import pandas as pd
import streamlit as st

from pubmedr import config
from pubmedr.ai_methods import s2_process_chat, s3_process_chat
from pubmedr.constants import MOCK_DATA
from pubmedr.data_models import (
    S1Setup,
    S2SettingsSimple,
    S3Queries,
    S5SavedResult,
    S5StateSnapshot,
)
from pubmedr.gdrive import read_all_entries, write_search_result
from pubmedr.metapub_methods import fetch_pubmed_results
from pubmedr.streamlit_components import (
    S0_SidebarSettings,
    S1_ResearcherSetup,
    S2_Advanced,
    S2_PubmedSearchSettings,
    S3_CodeEditor,
    S4SearchResults,
)

logger = config.custom_logger(__name__)


@st.cache_data(ttl=3600)
def read_readme():
    """Cache readme file reading."""
    return (Path(__file__).parent.parent / "README.md").read_text()


@logfire.instrument("Run PubMed Query", extract_args=True)
def run_query(query_text: str, status_container):
    """Run a single query and update results."""
    if not query_text or query_text.isspace():
        with status_container:
            st.warning("Empty query - skipping", icon="⚠️")
            time.sleep(1)  # Give user time to see the message
        return

    # Initialize cache in session state if not present
    if "query_cache" not in st.session_state:
        st.session_state.query_cache = set()

    if query_text in st.session_state.query_cache:
        with status_container:
            st.info("Query already run - skipping duplicate", icon="ℹ️")
            time.sleep(1)  # Give user time to see the message
        return

    with status_container, st.spinner("Fetching results..."):
        try:
            results = fetch_pubmed_results(query_text, max_results=15)
            logger.info("Found %d results for query %s", len(results), query_text)
            if not results:
                st.warning("No results found for this query", icon="⚠️")
                time.sleep(1.5)  # Give more time for no-results message
                return

            st.session_state.search_results.append(
                {
                    "query": query_text,
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            st.session_state.query_cache.add(query_text)
            st.success(f"Found {len(results)} results")
            time.sleep(0.5)  # Brief pause to show success message

        except Exception as e:
            st.error(f"Error fetching results: {e}", icon="🚨")
            time.sleep(0.5)


def get_selected_queries():
    """Get currently selected queries, with explicit state check."""
    selected = []
    for q in st.session_state.queries:
        if q.is_displayed:
            # Double check the checkbox state
            checkbox_key = f"select_{q.uid}"
            is_selected = st.session_state.get(checkbox_key, False)
            q.is_selected = is_selected  # Update query object
            if is_selected:
                selected.append(q)
    return selected


def update_all_query_contents():
    """Process content from code editors after Save is clicked."""
    displayed_queries = [q for q in st.session_state.queries if q.is_displayed]
    for q in displayed_queries:
        editor_key = f"editor_{q.uid}"
        response = st.session_state.get(editor_key)
        if response and isinstance(response, dict):
            updated_text = response.get("text", q.query_text)
            full_idx = next(i for i, sq in enumerate(st.session_state.queries) if sq.uid == q.uid)
            st.session_state.queries[full_idx].query_text = updated_text


@st.cache_data(ttl=3600)
def get_state_snapshot() -> S5StateSnapshot:
    """Cache the state snapshot for reuse."""
    # Get settings with fallback
    settings = st.session_state.get("settings")
    if not settings:
        settings = S2SettingsSimple()

    # Get setup with fallback
    setup = st.session_state.get("setup")
    if not setup:
        setup = S1Setup(
            s1_gsheet_id=config.GSHEET_ID,
            s1_researcher_background=MOCK_DATA["setup"]["researcher_background"],
            s1_researcher_goal=MOCK_DATA["setup"]["research_goal"],
        )

    # Safely get editor states
    editor_states = {}
    for q in st.session_state.get("queries", []):
        if not q.is_displayed:
            continue
        editor_key = f"editor_{q.uid}"
        editor_data = st.session_state.get(editor_key, {})
        if isinstance(editor_data, dict):
            editor_states[q.uid] = editor_data.get("text", q.query_text)
        else:
            editor_states[q.uid] = q.query_text

    return S5StateSnapshot(
        s0_is_advanced_mode=st.session_state.get("is_andvanced", False),
        s1_setup=setup,
        s2_settings=settings,
        s3_editor_states=editor_states,
        s3_query=None,
        s4_result=None,
    )


@logfire.instrument("Save to GSheet", extract_args=True)
def save_result_to_sheet(result, note: str, query: str, group_idx: int):
    """Save a single result with its metadata to Google Sheet."""
    try:
        result_group = st.session_state.search_results[group_idx]
        query_model = S3Queries(query_text=result_group["query"])

        # Get cached state snapshot
        state = get_state_snapshot()
        state.s3_query = query_model
        state.s4_result = result

        saved_result = S5SavedResult.from_staged_state(
            result=result,
            note=note or "",
            query=query_model,
            results_count=len(result_group["results"]),
            state=state,
        )

        row_data = saved_result.to_sheet_row()
        success, timestamp = write_search_result(
            sheet_id=config.GSHEET_ID,
            sheet_name=MOCK_DATA["setup"]["sheet_name"],
            result_data=row_data,
        )

        if success:
            # Update in-memory dataframe
            if "saved_papers_df" not in st.session_state:
                st.session_state.saved_papers_df = load_saved_results_df()

            # Create cleaned row without state snapshot
            cleaned_row = {k: v for k, v in row_data.items() if k != "s5_state_snapshot"}
            new_row_df = pd.DataFrame([cleaned_row])

            st.session_state.saved_papers_df = pd.concat(
                [st.session_state.saved_papers_df, new_row_df],
                ignore_index=True,
            )
            st.toast("Result saved successfully!", icon="✅")
        else:
            st.error("Failed to save result")

    except Exception as e:
        st.error(f"Failed to create saved result: {str(e)}")


def save_button(note_key: str, result, query: str, group_idx: int):
    if st.button("Save paper (with note)", key=f"save_{note_key}"):
        note = st.session_state.get(note_key, "")
        save_result_to_sheet(result, note, query, group_idx)


def restore_from_saved(saved_row: dict):
    """Restore application state from a saved result."""
    if "s5_state_snapshot" in saved_row:
        state = S5StateSnapshot.model_validate_json(saved_row["s5_state_snapshot"])
        # Restore each component's state
        st.session_state.setup = state.s1_setup
        st.session_state.settings = state.s2_settings
        st.session_state.queries = [state.s3_query]  # Just the single query
        st.session_state.is_andvanced = state.s0_is_advanced_mode
        # Restore editor states on next render
        for uid, content in state.s3_editor_states.items():
            st.session_state[f"editor_{uid}"] = {"text": content}


def run_selected_queries(status_container, merge_type: str | None = None):
    """Run selected queries with optional merging."""
    update_all_query_contents()
    selected = get_selected_queries()
    if not selected:
        with status_container:
            st.warning("No queries selected")
        return

    if merge_type == "OR":
        query = " OR ".join(f"({q.query_text})" for q in selected)
        run_query(query, status_container)
    elif merge_type == "AND":
        query = " AND ".join(f"({q.query_text})" for q in selected)
        run_query(query, status_container)
    else:
        for q in selected:
            run_query(q.query_text, status_container)

    st.rerun()


@logfire.instrument("Process S2 Chat Input", extract_args=True)
def process_s2_chat_input(chat_input: str):
    """Process chat input for S2 and update state."""
    if not chat_input:
        return

    try:
        # Add user message to history
        add_chat_message("user", chat_input)

        # Get current settings
        current_settings = {}
        if "settings" in st.session_state:
            current_settings = st.session_state.settings.model_dump() if hasattr(st.session_state.settings, "model_dump") else st.session_state.settings

        # Update with individual field if it exists
        if "keywords" in st.session_state:
            current_settings["keywords"] = st.session_state["keywords"]

        setup = S1Setup(
            s1_gsheet_id=st.session_state.get("gsheet_id", ""),  # s1_gsheet_id=config.GSHEET_ID,
            s1_researcher_background=st.session_state.get("researcher_background", ""),
            s1_researcher_goal=st.session_state.get("researcher_goal", ""),
        )

        result = s2_process_chat(
            setup=setup.model_dump(),
            settings=current_settings,
            chat_input=chat_input,
            is_advanced=st.session_state.get("is_advanced", False),
        )

        # Update settings
        if result.updated_settings:
            settings_dict = result.updated_settings.model_dump()
            logger.info("Updating settings with:", extra={"settings": settings_dict})

            if "keywords" in settings_dict:
                st.session_state.keywords_storage = settings_dict["keywords"]
            if "authors" in settings_dict:
                st.session_state.authors_storage = settings_dict["authors"]
            if "exclusions" in settings_dict:
                st.session_state.exclusions_storage = settings_dict["exclusions"]
            if "text_availability" in settings_dict:
                st.session_state.text_availability_storage = settings_dict["text_availability"]
            if "system_prompt" in settings_dict:
                st.session_state.system_prompt_storage = settings_dict["system_prompt"]
            if "n_queries_to_generate" in settings_dict:
                st.session_state.query_count_storage = settings_dict["n_queries_to_generate"]
            if "n_results_limit_per_query" in settings_dict:
                st.session_state.results_per_query_storage = settings_dict["n_results_limit_per_query"]

        if result.initial_queries:
            for query in result.initial_queries:
                st.session_state.queries.append(S3Queries(query_text=query))
            logger.info("Added queries", extra={"queries": result.initial_queries})

        add_chat_message("assistant", "Settings updated and queries generated!")
        st.rerun()  # Force UI refresh

    except Exception as e:
        logger.error("Failed to process chat input: %s", e, exc_info=True)
        st.error(f"Failed to process chat input: {str(e)}")


@logfire.instrument("Process S3 Chat Input", extract_args=True)
def process_s3_chat_input(chat_input: str):
    """Process chat input for query generation."""
    try:
        # Add user message to chat
        add_chat_message("user", chat_input)

        # Get current state
        setup = MOCK_DATA["setup"]  # TODO: Get from state
        settings = st.session_state.get("settings", {})
        current_queries = [q.query_text for q in st.session_state.queries if q.is_displayed]
        is_advanced = st.session_state.get("is_advanced", False)

        # Process chat with AI
        result = s3_process_chat(
            setup=setup,
            settings=settings,
            chat_input=chat_input,
            current_queries=current_queries,
            is_advanced=is_advanced,
        )

        # Add new queries to state
        if result.new_queries:
            for query in result.new_queries:
                st.session_state.queries.append(S3Queries(query_text=query))
            logger.info("Added queries", extra={"queries": result.new_queries})

        add_chat_message("assistant", "New queries generated!")
        st.rerun()  # Force UI refresh

    except Exception as e:
        logger.error("Failed to process chat input: %s", e, exc_info=True)
        st.error(f"Failed to process chat input: {str(e)}")


def init_chat_state():
    """Initialize chat-related session state."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "s2"  # Default to settings mode


def display_chat_history():
    """Display all messages in chat history."""
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def add_chat_message(role: str, content: str):
    """Add a message to chat history."""
    st.session_state.chat_history.append({"role": role, "content": content})


def load_saved_results_df():
    """Load and clean the saved results dataframe."""
    # Check if we have a cached dataframe
    if "saved_papers_df" in st.session_state:
        return st.session_state.saved_papers_df

    # Load from Google Sheet
    records = read_all_entries(config.GSHEET_ID)
    if not records:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(records)
        # Drop the state snapshot and other unnecessary columns
        columns_to_keep = [
            "s4_paper_title",
            "s4_paper_authors",
            "s4_paper_year",
            "s4_paper_journal",
            "s4_paper_pubmed_url",
            "s1_researcher_goal",
            "s3_search_query",
            "s5_user_note",
        ]
        df = df[columns_to_keep].copy()

    # Cache the dataframe
    st.session_state.saved_papers_df = df
    return df


def restore_state_from_snapshot(row_idx: int):
    """Restore UI state from a saved snapshot."""
    # Get full records including state snapshot
    records = read_all_entries(config.GSHEET_ID)
    if not records or row_idx >= len(records):
        st.error("Could not restore state")
        return

    saved_state = records[row_idx].get("s5_state_snapshot")
    if not saved_state:
        st.error("No state snapshot found")
        return

    try:
        state = S5StateSnapshot.model_validate_json(saved_state)
        # Restore state components
        st.session_state.setup = state.s1_setup
        st.session_state.settings = state.s2_settings
        st.session_state.queries = [state.s3_query] if state.s3_query else []
        st.session_state.is_advanced = state.s0_is_advanced_mode
        # Restore editor states
        for uid, content in state.s3_editor_states.items():
            st.session_state[f"editor_{uid}"] = {"text": content}
        st.rerun()
    except Exception as e:
        st.error(f"Failed to restore state: {str(e)}")


def main():
    st.set_page_config(layout="wide")
    st.title("PubMedR - PubMed Research Assistant UI")

    # Initialize session state
    if "queries" not in st.session_state:
        st.session_state.queries = [S3Queries(query_text=q) for q in MOCK_DATA["queries"]]
    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    with st.sidebar:
        with st.popover("View Readme"):
            st.markdown(read_readme())

        st.button("Save Current Settings")
        st.markdown(f"[Open Google Sheet (Persistent Database)](https://docs.google.com/spreadsheets/d/{MOCK_DATA['setup']['gsheet_id']})")

        init_chat_state()
        is_advanced = S0_SidebarSettings.search_settings()
        st.session_state.is_andvanced = is_advanced

        operation = S0_SidebarSettings.chat_operation()
        st.session_state.chat_mode = operation
        display_chat_history()

        # Chat input
        chat_input = st.chat_input("Give instructions or ask questions...")
        if chat_input:
            if operation == "s2":
                process_s2_chat_input(chat_input)
            elif operation == "s3":
                process_s3_chat_input(chat_input)
            elif operation == "s5":
                st.info("Paper analysis coming soon!")  # TODO

        # TODO: Add a button to clear the chat history

    st.header("1. Researcher Setup")
    with st.container(border=True, key="researcher_setup"):
        col1, col2 = st.columns(2)
        with col1:
            S1_ResearcherSetup.background()
        with col2:
            S1_ResearcherSetup.goal()

    st.header("2. Pubmed Search Settings")
    with st.container(border=True, key="pubmed_search_settings"):
        settings = None
        if "settings" in st.session_state:
            settings = st.session_state.settings.model_dump() if hasattr(st.session_state.settings, "model_dump") else st.session_state.settings

        keywords = S2_PubmedSearchSettings.keywords(settings)
        if keywords:
            st.session_state["keywords"] = keywords

        S2_PubmedSearchSettings.year_range()

        col1, col2 = st.columns(2)
        with col1:
            S2_PubmedSearchSettings.authors()
        with col2:
            S2_PubmedSearchSettings.exclusions()

        col1, _, col2, _, col3 = st.columns([44, 6, 22, 6, 22])
        with col1:
            S2_PubmedSearchSettings.text_availability()
        with col2:
            S2_PubmedSearchSettings.query_count()
        with col3:
            S2_PubmedSearchSettings.results_per_query()

        S2_PubmedSearchSettings.system_prompt()

    with st.expander("Advanced Settings (enable in sidebar)", expanded=is_advanced):
        col1, col2 = st.columns(2)
        with col1:
            S2_Advanced.first_author(is_advanced)
            S2_Advanced.last_author(is_advanced)
            S2_Advanced.pub_types(is_advanced)
            S2_Advanced.article_types(is_advanced)
            S2_Advanced.species(is_advanced)
            S2_Advanced.gender(is_advanced)
        with col2:
            S2_Advanced.proximity(is_advanced)
            S2_Advanced.identifiers(is_advanced)
            S2_Advanced.affiliations(is_advanced)
            S2_Advanced.substance(is_advanced)
            S2_Advanced.mesh_terms(is_advanced)

    st.header("3. Query Management")
    with st.container(border=True, key="query_management"):
        displayed_queries = [q for q in st.session_state.queries if q.is_displayed]

        for idx, query in enumerate(displayed_queries):
            with st.container():
                col1, col2 = st.columns([95, 5])
                with col1:
                    response = S3_CodeEditor.editor_config(
                        query.query_text,
                        key=f"editor_{query.uid}",
                    )
                    if response["type"] == "submit":
                        update_all_query_contents()
                with col2:
                    was_selected = query.is_selected
                    is_selected = st.checkbox(
                        "Select query for processing",
                        value=query.is_selected,
                        key=f"select_{query.uid}",
                        label_visibility="collapsed",
                    )
                    # Explicitly update selection state
                    full_idx = next(i for i, sq in enumerate(st.session_state.queries) if sq.uid == query.uid)
                    st.session_state.queries[full_idx].is_selected = is_selected
                    if was_selected != is_selected:  # If selection changed
                        st.rerun()  # Force refresh

        # Action buttons
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        status_container = st.container()

        with col1:
            if st.button("Add New Field", type="secondary"):
                st.session_state.queries.append(S3Queries(query_text=""))
                st.rerun()
        with col2:
            if st.button("Select All/None", type="secondary"):
                all_selected = all(q.is_selected for q in st.session_state.queries if q.is_displayed)
                for q in st.session_state.queries:
                    if q.is_displayed:
                        q.is_selected = not all_selected
        with col3:
            if st.button("Delete Selected", type="secondary"):
                for q in st.session_state.queries:
                    if q.is_selected:
                        q.is_displayed = False
                st.rerun()

    with col4:
        if st.button("Run Individually", type="primary"):
            run_selected_queries(status_container)

    with col5:
        if st.button("Run Merged (OR)", type="primary"):
            run_selected_queries(status_container, "OR")

    with col6:
        if st.button("Run Merged (AND)", type="primary"):
            run_selected_queries(status_container, "AND")

    # Section 4: Search Results
    st.header("4. Search Results")
    with st.container(border=True, key="search_results"):
        if "search_results" in st.session_state:
            for group_idx, result_group in enumerate(st.session_state.search_results):
                timestamp = datetime.fromisoformat(result_group["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                with st.expander(
                    f"{len(result_group['results'])} Results  —  {timestamp}" f"\n{result_group['query']}",
                    expanded=True,
                ):
                    for idx, result in enumerate(result_group["results"]):
                        with st.container(border=True):
                            col1, col2 = st.columns([30, 70])
                            with col1:
                                # Make key unique by combining group_idx, timestamp, and result idx
                                note_key = f"note_group{group_idx}_{result_group['timestamp']}_{idx}"
                                S4SearchResults.research_notes(note_key)
                                save_button(
                                    note_key,
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

    # Section 5: Saved Papers
    st.header("5. Saved Papers")
    with st.container(border=True, key="saved_papers"):
        # Load the dataframe
        df = load_saved_results_df()

        if df.empty:
            st.info("No saved papers yet")
        else:
            # Add restore buttons column
            df_with_buttons = df.copy()
            for idx in range(len(df)):
                restore_key = f"restore_state_{idx}"
                if st.button("Restore", key=restore_key):
                    restore_state_from_snapshot(idx)

            # Display the cleaned dataframe
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "s4_paper_pubmed_url": st.column_config.LinkColumn("PubMed Link"),
                    "s4_paper_title": st.column_config.TextColumn("Title", width="large"),
                    "s4_paper_authors": st.column_config.TextColumn("Authors", width="medium"),
                    "s4_paper_year": st.column_config.TextColumn("Year", width="small"),
                    "s4_paper_journal": st.column_config.TextColumn("Journal", width="medium"),
                    "s1_researcher_goal": st.column_config.TextColumn("Research Goal", width="medium"),
                    "s3_search_query": st.column_config.TextColumn("Search Query", width="medium"),
                    "s5_user_note": st.column_config.TextColumn("Notes", width="medium"),
                },
                hide_index=True,
            )


if __name__ == "__main__":
    main()
