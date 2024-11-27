# ./src/pubmedr/main_streamlit.py
# Streamlit version of pubmedr, created to avoid UI issues with Textual.


# app.py

import streamlit as st
import pandas as pd
from pubmedr.data_models import (
    S1datamodelSetup,
    S2datamodelSettingsSimple,
    S2datamodelSettingsAdvanced,
    S2datamodelSettings,
    # Add other necessary imports
)
from pubmedr.ai_methods import run_llm_job
from pubmedr.gdrive import read_all_entries, write_all_data
from pubmedr.config import GOOGLE_CLOUD_CREDENTIALS
import pubmedr.data_store as data_store  # Assuming this is where you store your data models
from gspread_dataframe import set_with_dataframe
import json

# Initialize data models
if "s1_setup_data" not in st.session_state:
    st.session_state.s1_setup_data = S1datamodelSetup(
        s1_gsheet_id="", s1_researcher_background="", s1_researcher_goal=""
    )

if "s2_settings_data" not in st.session_state:
    st.session_state.s2_settings_data = S2datamodelSettings()

if "queries" not in st.session_state:
    st.session_state.queries = []

if "selected_queries" not in st.session_state:
    st.session_state.selected_queries = []

if "results" not in st.session_state:
    st.session_state.results = {}

if "saved_papers" not in st.session_state:
    st.session_state.saved_papers = []


# Helper functions
def format_gsheet_url(gsheet_id):
    return f"https://docs.google.com/spreadsheets/d/{gsheet_id}/edit?usp=sharing"


def extract_gsheet_id(url_or_id):
    # Your implementation to extract the Google Sheet ID
    pass


def save_setup_to_gsheet(setup_data):
    # Use your existing function to save data to Google Sheet
    success, timestamp_uid = write_all_data(sheet_id=setup_data.s1_gsheet_id, sheet_name="data")
    return success


def load_saved_entries():
    # Use your existing function to read entries from Google Sheet
    entries = read_all_entries(sheet_id=st.session_state.s1_setup_data.s1_gsheet_id, sheet_name="data")
    return entries


def run_queries(queries):
    # Your implementation to run queries and get results
    pass


def save_paper(paper, note):
    # Your implementation to save paper with note
    pass


# Main sections
def setup_section():
    st.header("Setup")
    st.text_input("Google Sheet ID or URL", key="s1_gsheet_id", value=st.session_state.s1_setup_data.s1_gsheet_id)
    st.text_input(
        "Researcher Background",
        key="s1_researcher_background",
        value=st.session_state.s1_setup_data.s1_researcher_background,
    )
    st.text_input(
        "Specific Research Goal", key="s1_researcher_goal", value=st.session_state.s1_setup_data.s1_researcher_goal
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Setup"):
            # Update data model
            st.session_state.s1_setup_data = S1datamodelSetup(
                s1_gsheet_id=st.session_state.s1_gsheet_id,
                s1_researcher_background=st.session_state.s1_researcher_background,
                s1_researcher_goal=st.session_state.s1_researcher_goal,
            )
            # Save to Google Sheet
            success = save_setup_to_gsheet(st.session_state.s1_setup_data)
            if success:
                st.success("Setup saved successfully!")
            else:
                st.error("Failed to save setup.")
    with col2:
        if st.button("Open Google Sheet"):
            gsheet_url = format_gsheet_url(st.session_state.s1_setup_data.s1_gsheet_id)
            st.markdown(f"[Open Google Sheet]({gsheet_url})")


def settings_section():
    st.header("Settings")
    # Smart UI components
    # Date range slider
    start_year, end_year = st.slider("Year Range", 1750, 2026, (2000, 2020))
    st.session_state.s2_settings_data.start_year = start_year
    st.session_state.s2_settings_data.end_year = end_year

    # Radio buttons
    st.session_state.s2_settings_data.text_availability = st.radio(
        "Text Availability", options=["all", "hasabstract", "free full text[sb]", "full text[sb]"]
    )
    st.session_state.s2_settings_data.gender = st.radio("Gender", options=["Male", "Female", "Both"])
    st.session_state.s2_settings_data.species = st.radio("Species", options=["Humans", "Other Animals", "Both"])

    # Proximity search
    proximity_search_enabled = st.radio("Proximity Search Enabled", options=["Yes", "No"])
    st.session_state.s2_settings_data.proximity_search_enabled = proximity_search_enabled == "Yes"
    if st.session_state.s2_settings_data.proximity_search_enabled:
        st.session_state.s2_settings_data.proximity_distance = st.number_input(
            "Proximity Distance", min_value=0, value=10
        )

    # Result limit
    st.session_state.s2_settings_data.result_limit = st.number_input("Result Limit", min_value=1, value=500)

    # Other settings
    # Add more inputs as needed based on your data models


def queries_section():
    st.header("Queries")
    # Left sidebar chat UI
    with st.sidebar:
        st.subheader("Chat")
        chat_mode = st.radio("Chat Mode", ["Refine Settings", "Refine Queries", "Chat"])
        chat_input = st.text_input("Type your message:")
        if st.button("Send"):
            if chat_input.strip() != "":
                if chat_mode == "Refine Settings":
                    # Call AI method to refine settings
                    input_data = {
                        "current_settings": st.session_state.s2_settings_data.dict(),
                        "chat_input": chat_input,
                    }
                    input_json = json.dumps(input_data)
                    result = run_llm_job("s2_advanced", input_json)
                    # Update settings
                    st.session_state.s2_settings_data = S2datamodelSettings(**result.updated_settings)
                    st.success("Settings updated based on your input.")
                elif chat_mode == "Refine Queries":
                    # Call AI method to refine queries
                    input_data = {
                        "search_settings": st.session_state.s2_settings_data.dict(),
                        "recent_queries": st.session_state.queries,
                        "chat_input": chat_input,
                    }
                    input_json = json.dumps(input_data)
                    result = run_llm_job("s3_advanced", input_json)
                    # Update queries
                    st.session_state.queries = result.new_queries
                    st.success("Queries updated based on your input.")
                elif chat_mode == "Chat":
                    # Display chat response
                    input_data = {"content": chat_input}
                    input_json = json.dumps(input_data)
                    result = run_llm_job("s5", input_json)
                    st.markdown(result.answer)
            else:
                st.error("Please enter a message.")

    # Display queries
    st.subheader("Generated Queries")
    if st.session_state.queries:
        cols = st.columns(3)
        for idx, query in enumerate(st.session_state.queries):
            col = cols[idx % 3]
            with col:
                # Editable code block
                edited_query = st.text_area(f"Query {idx+1}", value=query, key=f"query_{idx}")
                st.session_state.queries[idx] = edited_query
                # Select/Deselect
                selected = st.checkbox("Select", key=f"select_{idx}", value=False)
                if selected:
                    if edited_query not in st.session_state.selected_queries:
                        st.session_state.selected_queries.append(edited_query)
                else:
                    if edited_query in st.session_state.selected_queries:
                        st.session_state.selected_queries.remove(edited_query)
                # Run button
                if st.button("Run This Query", key=f"run_{idx}"):
                    # Run the individual query
                    results = run_queries([edited_query])
                    st.session_state.results[edited_query] = results
                    st.success(f"Query {idx+1} executed.")
        # Buttons for all queries
        if st.button("Run All Selected Queries"):
            results = run_queries(st.session_state.selected_queries)
            for query, res in zip(st.session_state.selected_queries, results):
                st.session_state.results[query] = res
            st.success("All selected queries executed.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All"):
                st.session_state.selected_queries = st.session_state.queries.copy()
        with col2:
            if st.button("Deselect All"):
                st.session_state.selected_queries = []
    else:
        st.info("No queries generated yet.")


def results_section():
    st.header("Results")
    # Display results for each query
    for query, articles in st.session_state.results.items():
        with st.expander(f"Results for Query: {query}"):
            for idx, article in enumerate(articles):
                st.markdown("---")
                st.write(f"**Title**: {article['title']}")
                st.write(f"**Authors**: {article['authors']}")
                st.write(f"**Abstract**: {article['abstract']}")
                st.write(f"**Year**: {article['year']}")
                st.write(f"**Journal**: {article['journal']}")
                note = st.text_input("Note", key=f"note_{article['id']}")
                if st.button("Save Paper with Note", key=f"save_{article['id']}"):
                    save_paper(article, note)
                    st.success("Paper saved.")


def saved_section():
    st.header("Saved Papers")
    # Display saved papers
    if st.session_state.saved_papers:
        df = pd.DataFrame(st.session_state.saved_papers)
        st.dataframe(df)
        if st.button("Reload Settings from Selected Entry"):
            # Implement functionality to reload settings
            selected_indices = st.multiselect("Select entries to reload settings", options=df.index.tolist())
            if selected_indices:
                selected_entry = df.iloc[selected_indices[0]].to_dict()
                # Update settings based on selected entry
                st.session_state.s1_setup_data = S1datamodelSetup(
                    s1_gsheet_id=selected_entry.get("s1_gsheet_id", ""),
                    s1_researcher_background=selected_entry.get("s1_researcher_background", ""),
                    s1_researcher_goal=selected_entry.get("s1_researcher_goal", ""),
                )
                # Similarly update other settings
                st.success("Settings reloaded from selected entry.")
    else:
        st.info("No saved papers yet.")


# Main app
def main():
    st.set_page_config(layout="wide")
    st.title("PubMed Research Assistant")
    menu = ["Setup", "Settings", "Queries", "Results", "Saved"]
    choice = st.sidebar.selectbox("Menu", menu)
    if choice == "Setup":
        setup_section()
    elif choice == "Settings":
        settings_section()
    elif choice == "Queries":
        queries_section()
    elif choice == "Results":
        results_section()
    elif choice == "Saved":
        saved_section()


if __name__ == "__main__":
    main()
