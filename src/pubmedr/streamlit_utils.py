# ./pubmedr/streamlit_utils.py

import time
from datetime import datetime
from typing import Any

import logfire
import pandas as pd
import streamlit as st

from pubmedr import config
from pubmedr.ai_methods import s2_process_chat, s3_process_chat, s4_question_answer
from pubmedr.config import logger
from pubmedr.constants import MOCK_DATA
from pubmedr.data_models import (
    S1Setup,
    S2Query,
    S2Settings,
    S2SettingsSimple,
    S4Results,
    S5SavedResult,
    S5StateSnapshot,
    Settings,
)
from pubmedr.gdrive import read_all_entries, read_latest_settings, write_search_result, write_settings
from pubmedr.metapub_methods import fetch_pubmed_results
from pubmedr.streamlit_components import S5_SavedPapers


def s0_init_session_state():
    """Initialize all session state variables."""
    if "queries" not in st.session_state:
        st.session_state.queries = [S2Query(query_text=q) for q in MOCK_DATA["queries"]]
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "setup" not in st.session_state:
        st.session_state.setup = S1Setup(
            s1_gsheet_id=config.GSHEET_ID,
            s1_researcher_background="",
            s1_researcher_goal="",
        )
    if "settings" not in st.session_state:
        st.session_state.settings = Settings()


def s0_load_settings() -> None:
    """Load most recent settings from gsheet."""
    try:
        settings_data = read_latest_settings(config.GSHEET_ID)
        if settings_data and "settings_snapshot" in settings_data:
            state = S5StateSnapshot.model_validate_json(settings_data["settings_snapshot"])

            # Update both memory and session state
            st.session_state.setup = state.s1_setup
            st.session_state.settings = Settings(**state.s2_settings.model_dump())
            st.session_state.queries = [state.s2_query] if state.s2_query else []
            st.session_state.is_advanced = state.s0_is_advanced_mode

            # Update all UI widget states
            for key, value in state.s2_settings.model_dump().items():
                st.session_state[f"{key}_storage"] = value

            # Update researcher fields in session state
            st.session_state["researcher_background"] = state.s1_setup.s1_researcher_background
            st.session_state["researcher_goal"] = state.s1_setup.s1_researcher_goal
            st.session_state["gsheet_id"] = state.s1_setup.s1_gsheet_id

            # Update editor states
            for uid, content in state.s3_editor_states.items():
                st.session_state[f"editor_{uid}"] = {"text": content}

            st.toast("✅ Settings loaded successfully!", icon="✅")
            st.rerun()
        else:
            st.toast("ℹ️ No settings found to load", icon="ℹ️")
    except Exception:
        logger.error("Failed to load settings", exc_info=True)
        st.toast("❌ Failed to load settings", icon="❌")


def s0_save_settings() -> None:
    """Save current settings to gsheet."""
    try:
        # Get everything from session state
        settings_dict = st.session_state.get("settings", Settings()).model_dump()
        is_advanced = st.session_state.get("is_advanced", False)

        # Create setup from session state UI values
        setup = S1Setup(
            s1_gsheet_id=st.session_state.get("gsheet_id", config.GSHEET_ID),
            s1_researcher_background=st.session_state.get("researcher_background", ""),
            s1_researcher_goal=st.session_state.get("researcher_goal", ""),
        )

        # Convert settings based on mode
        settings_cls = S2Settings if is_advanced else S2SettingsSimple
        converted_settings = settings_cls(**settings_dict)

        # Safely get editor states
        editor_states = {}
        for k, v in st.session_state.items():
            if isinstance(k, str) and k.startswith("editor_") and isinstance(v, dict):
                editor_states[k] = v.get("text", "")

        # Create state snapshot
        state = S5StateSnapshot(
            s0_is_advanced_mode=is_advanced,
            s1_setup=setup,
            s2_settings=converted_settings,
            s2_query=st.session_state.get("queries", [S2Query()])[0],
            s3_editor_states=editor_states,
        )

        # Create settings data
        settings_data = {
            "settings": settings_dict,
            "is_advanced": is_advanced,
            "setup": setup.model_dump(),
            "settings_snapshot": state.model_dump_json(),
        }

        success, timestamp = write_settings(setup.s1_gsheet_id, settings_data)

        if success:
            st.toast("✅ Settings saved successfully!", icon="✅")
            logger.info("Settings saved", extra={"settings": settings_data})
        else:
            st.toast("❌ Failed to save settings", icon="❌")

    except Exception as e:
        logger.error(f"Failed to save settings: {str(e)}", exc_info=True)
        st.toast(f"❌ Failed to save: {str(e)}", icon="❌")


def s0_add_chat_message(role: str, content: str):
    """Add a message to chat history."""
    st.session_state.chat_messages.append({"role": role, "content": content})


def s2_get_settings_value(key: str, default: Any = None) -> Any:
    """Get a value from UI settings, with fallback."""
    if "settings" not in st.session_state:
        st.session_state.settings = Settings()
    return st.session_state.settings.get(key, default)


def s2_prase_chat(chat_input: str):
    """Process chat input for settings updates."""
    try:
        s0_add_chat_message("user", chat_input)

        # Initialize or get UI settings
        if "settings" not in st.session_state:
            st.session_state.settings = Settings()
        elif isinstance(st.session_state.settings, dict):
            st.session_state.settings = Settings(**st.session_state.settings)

        # Get setup data safely
        setup_data = {}
        if "setup" in st.session_state:
            setup = st.session_state.setup
            setup_data = setup.model_dump() if hasattr(setup, "model_dump") else setup

        settings_cls = S2Settings if st.session_state.get("is_advanced", False) else S2SettingsSimple
        current_settings = settings_cls(**st.session_state.settings.model_dump())

        result = s2_process_chat(
            setup=setup_data,
            settings=current_settings.model_dump(),
            chat_input=chat_input,
            is_advanced=st.session_state.get("is_advanced", False),
        )

        # Update UI settings from result
        if hasattr(result, "updated_settings"):
            st.session_state.settings = Settings(**result.updated_settings.model_dump())

        if hasattr(result, "queries") and result.queries:
            st.session_state.queries.extend(result.queries)
            logger.info("Added queries", extra={"queries": [q.query_text for q in result.queries]})

        if result.updated_settings or (hasattr(result, "queries") and result.queries):
            s0_add_chat_message("assistant", "Settings and queries updated!")
            st.rerun()
        else:
            logger.warning("No updates made from chat", extra={"result": result})
            st.warning("No updates were made from your input")

    except Exception as e:
        logger.error("Failed to process chat input", exc_info=True)
        st.error(f"Failed to process chat input: {str(e)}")


def s3_handle_chat_input(chat_input: str):
    """Process chat input for query generation."""
    try:
        s0_add_chat_message("user", chat_input)

        setup = st.session_state.get("setup", MOCK_DATA["setup"])
        settings = st.session_state.get("settings", Settings())
        current_queries = [q.query_text for q in st.session_state.queries if q.is_displayed]
        is_advanced = st.session_state.get("is_advanced", False)

        # Convert UI settings to appropriate AI model settings
        settings_cls = S2Settings if is_advanced else S2SettingsSimple
        current_settings = settings_cls(**settings.model_dump())

        result = s3_process_chat(
            setup=setup,
            settings=current_settings.model_dump(),  # Convert to dict for AI methods
            chat_input=chat_input,
            current_queries=current_queries,
            is_advanced=is_advanced,
        )

        if hasattr(result, "queries") and result.queries:
            new_queries = [q if isinstance(q, S2Query) else S2Query(query_text=q.query_text) for q in result.queries]
            st.session_state.queries.extend(new_queries)
            logger.info("Added queries", extra={"queries": [q.query_text for q in new_queries]})
            s0_add_chat_message("assistant", "New queries generated!")
            st.rerun()

    except Exception as e:
        logger.error("Failed to process chat input: %s", e, exc_info=True)
        st.error(f"Failed to process chat input: {str(e)}")


def s3_update_query_contents():
    """Update all query contents from editors to session state."""
    try:
        displayed_queries = [q for q in st.session_state.queries if q.is_displayed]
        for q in displayed_queries:
            editor_key = f"editor_{q.uid}"
            if editor_key in st.session_state and isinstance(st.session_state[editor_key], dict):
                new_text = st.session_state[editor_key].get("text", q.query_text)
                full_idx = next(i for i, sq in enumerate(st.session_state.queries) if sq.uid == q.uid)
                st.session_state.queries[full_idx].query_text = new_text
    except Exception:
        logger.error("Failed to sync editor contents", exc_info=True)
        raise


@logfire.instrument("Run PubMed Query", extract_args=True)
def _s3_run_single_query(query_text: str, status_container):
    """Run single PubMed query with caching."""
    if not query_text or query_text.isspace():
        with status_container:
            st.warning("Empty query - skipping", icon="⚠️")
            time.sleep(1)
        return

    if "query_cache" not in st.session_state:
        st.session_state.query_cache = set()

    if query_text in st.session_state.query_cache:
        with status_container:
            st.info("Query already run - skipping duplicate", icon="ℹ️")
            time.sleep(1)
        return

    with status_container, st.spinner("Fetching results..."):
        try:
            results = fetch_pubmed_results(query_text)
            if results:
                st.session_state.search_results.append(
                    {
                        "query": query_text,
                        "timestamp": datetime.now().isoformat(),
                        "results": results,
                    }
                )
                st.session_state.query_cache.add(query_text)
        except Exception as e:
            st.error(f"Query failed: {str(e)}")


@logfire.instrument("Run Selected Queries", extract_args=True)
def s3_run_selected_queries(status_container, merge_type: str | None = None):
    """Run selected queries with optional merging."""
    s3_update_query_contents()
    selected = [q for q in st.session_state.queries if q.is_displayed and q.is_selected]
    logger.info("Executing queries", extra={"selected": [q.query_text for q in selected], "merge_type": merge_type})
    if not selected:
        with status_container:
            st.warning("No queries selected")
        return

    if merge_type:
        operator = " OR " if merge_type == "OR" else " AND "
        merged_query = operator.join(f"({q.query_text})" for q in selected)
        _s3_run_single_query(merged_query, status_container)
    else:
        for q in selected:
            _s3_run_single_query(q.query_text, status_container)

    st.rerun()


def s4_note_tools(note_key: str, result: S4Results, query: str, group_idx: int):
    """Handle note-related tools (save and summarise)."""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Paper", key=f"save_{note_key}", type="primary", disabled=config.LOCK_GSHEET):
            s4_save_result(note_key, result, S2Query(query_text=query), group_idx)
    with col2:
        if st.button("Summarise!", key=f"summarise_{note_key}", type="secondary"):
            setup = st.session_state.get("setup")
            if not setup or not (setup.s1_researcher_background or setup.s1_researcher_goal):
                st.warning("No researcher background/goals set - summary will be generic", icon="⚠️")
                background = ""
                goal = ""
            else:
                background = setup.s1_researcher_background
                goal = setup.s1_researcher_goal

            question = f"Title: {result.title}\nAbstract: {result.abstract or 'No abstract available'}"
            if background or goal:
                question += f"\nResearcher Background: {background}\nResearcher Goal: {goal}"

            try:
                answer = s4_question_answer(question)
                if answer:
                    # Get existing note content using storage key
                    storage_key = f"{note_key}_storage"
                    current_note = st.session_state.get(storage_key, "")
                    # Format new content with timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    ai_summary = f"\n\nAI Summary ({timestamp}):\n{answer}"
                    # Update session state with combined content
                    st.session_state[storage_key] = f"{current_note}{ai_summary}" if current_note else ai_summary
                    st.rerun()
                else:
                    st.error("Failed to generate summary: No response from AI")
            except Exception as e:
                logger.error("Failed to generate summary", exc_info=True)
                st.error(f"Failed to summarize: {str(e)}")


def s4_save_result(note_key: str, result: S4Results, query: S2Query, group_idx: int) -> None:
    """Save a search result with its associated metadata."""
    try:
        # Get current note text
        note = st.session_state.get(note_key, "")

        # Get results count safely
        results_count = 0
        search_results = st.session_state.get("search_results", [])
        if 0 <= group_idx < len(search_results):
            results = search_results[group_idx].get("results", [])
            results_count = len(results)

        # Get current state with defaults
        setup = st.session_state.get(
            "setup",
            S1Setup(
                s1_gsheet_id=config.GSHEET_ID,
                s1_researcher_background="",
                s1_researcher_goal="",
            ),
        )
        settings = st.session_state.get("settings", Settings())
        is_advanced = st.session_state.get("is_advanced", False)

        # Create state snapshot
        state = S5StateSnapshot(
            s0_is_advanced_mode=is_advanced,
            s1_setup=setup,
            s2_settings=settings,
            s2_query=query,
            s3_editor_states={},  # Optional: Add editor states if needed
        )

        # Create saved result
        saved_result = S5SavedResult.from_staged_state(
            result=result,
            note=note,
            query=query,
            results_count=results_count,
            state=state,
        )

        # Write to storage
        success, _ = write_search_result(
            sheet_id=setup.s1_gsheet_id,
            sheet_name="data",
            result_data=saved_result.model_dump(),
        )

        if success:
            st.success("Saved successfully!")
        else:
            st.error("Failed to save")

    except Exception as e:
        logger.error(f"Failed to save result: {str(e)}", exc_info=True)
        st.error(f"Failed to save: {str(e)}")


def s5_load_results_df() -> pd.DataFrame:
    """Load and format saved results."""
    try:
        records = read_all_entries(config.GSHEET_ID)
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        return S5_SavedPapers.filter_columns(df)
    except Exception as e:
        logger.error("Failed to load saved results: %s", e)
        return pd.DataFrame()


def s5_restore_state(row_idx: int):
    """Restore UI state from a saved snapshot."""
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
        st.session_state.setup = state.s1_setup
        st.session_state.settings = Settings(**state.s2_settings.model_dump())
        st.session_state.queries = [state.s2_query] if state.s2_query else []
        st.session_state.is_advanced = state.s0_is_advanced_mode
        for uid, content in state.s3_editor_states.items():
            st.session_state[f"editor_{uid}"] = {"text": content}
        st.rerun()
    except Exception as e:
        st.error(f"Failed to restore state: {str(e)}")


def s5_process_chat(user_message: str, df: pd.DataFrame):
    """Process chat input for S5 (mock for now)."""
    s0_add_chat_message("user", user_message)
    s0_add_chat_message("assistant", "Paper analysis feature coming soon!")
    st.rerun()
