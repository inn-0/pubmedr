import uuid

import streamlit as st
from code_editor import code_editor
from pydantic import BaseModel, Field

from pubmedr.constants import INFO_BAR, INFO_BAR_BUTTONS, PUBMED_COMPLETIONS, STYLING_BUTTONS


class S3Query(BaseModel):
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = Field(
        ...,
        description="PubMed query string with proper syntax and formatting",
        examples=["Doktorova T AND (Triclosan[Substance Name] OR Triclosan[Title/Abstract])"],
    )
    is_selected: bool = Field(default=False)
    is_displayed: bool = Field(default=True)


def initialize_state():
    if "queries" not in st.session_state:
        st.session_state.queries = [S3Query(query_text=query) for query in SAMPLE_QUERIES]


# Sample PubMed queries
SAMPLE_QUERIES = [
    "Doktorova T[1au] \nAND (Triclosan[Substance Name] OR Triclosan[Title/Abstract])",
    "(Piperonyl Butoxide[nm] OR PBO[tiab]) \nAND hepatotoxicity[tiab] \nAND Humans[mh]",
    '"in vitro models"[Title/Abstract:~5] \nNOT China[ad]',
]


st.set_page_config(
    page_title="PubMed Query Editor",
    layout="wide",
)

# Remove button styling for big UI buttons
st.markdown(
    STYLING_BUTTONS,
    unsafe_allow_html=True,
)


def query_editor(query: S3Query, index: int):
    if not query.is_displayed:
        return

    col1, col2 = st.columns([95, 5])
    with col1:
        response = code_editor(
            query.query_text,
            lang="sql",
            height=100,
            theme="default",
            shortcuts="sublime",
            buttons=INFO_BAR_BUTTONS,
            info=INFO_BAR,
            options={
                "wrap": True,
                "fontSize": 14,
                "enableBasicAutocompletion": True,
                "enableLiveAutocompletion": True,
                "showGutter": False,
                "highlightActiveLine": True,
                "showPrintMargin": False,
            },
            completions=PUBMED_COMPLETIONS,
            key=f"editor_{query.uid}",
        )
    with col2:
        st.session_state.queries[index].is_selected = st.checkbox(
            "Select query",
            value=query.is_selected,
            key=f"select_{query.uid}",
            label_visibility="collapsed",
        )

    if response["type"] == "submit":
        st.session_state.run_query = query.query_text
    elif response["type"] == "delete":
        st.session_state.queries[index].is_displayed = False
        st.experimental_rerun()


def main():
    st.title("PubMed Query Editor Demo")

    initialize_state()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("Select All/None", type="secondary"):
            all_selected = all(query.is_selected for query in st.session_state.queries if query.is_displayed)
            for query in st.session_state.queries:
                if query.is_displayed:
                    query.is_selected = not all_selected
    with col2:
        if st.button("Delete Selected", type="secondary"):
            for query in st.session_state.queries:
                if query.is_selected:
                    query.is_displayed = False
            st.rerun()
    with col3:
        if st.button("Run Individually", type="primary"):
            for query in st.session_state.queries:
                if query.is_selected and query.is_displayed:
                    st.session_state.run_query = query.query_text
                    st.subheader("Query Executed:")
                    st.code(st.session_state.run_query, language="text")
    with col4:
        if st.button("Run Merged (OR)", type="primary"):
            selected_queries = [
                query.query_text for query in st.session_state.queries if query.is_selected and query.is_displayed
            ]
            if selected_queries:
                st.session_state.run_query = "\n\nOR\n\n".join(f"({query})" for query in selected_queries)
                st.subheader("Query Executed:")
                st.code(st.session_state.run_query, language="text")
            else:
                st.warning("No queries selected")
    with col5:
        if st.button("Run Merged (AND)", type="primary"):
            selected_queries = [
                query.query_text for query in st.session_state.queries if query.is_selected and query.is_displayed
            ]
            if selected_queries:
                st.session_state.run_query = "\n\nAND\n\n".join(f"({query})" for query in selected_queries)
                st.subheader("Query Executed:")
                st.code(st.session_state.run_query, language="text")
            else:
                st.warning("No queries selected")

    for idx, query in enumerate(st.session_state.queries):
        if query.is_displayed:
            with st.container():
                query_editor(query, idx)

    if "run_query" in st.session_state:
        st.subheader("Query Executed:")
        st.code(st.session_state.run_query, language="text")
        del st.session_state.run_query


if __name__ == "__main__":
    main()
