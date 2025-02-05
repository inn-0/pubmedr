# **PubMedR - AI-Enhanced PubMed Researcher Assistant UI**


---

## **Live Demo**

[PubMedR Live Website](https://pubmedr.replit.app) ↓ Click Image for Summary Video ↓
[![PubMedR Video](https://github.com/inn-0/pubmedr/blob/main/assets/PubMedR.jpg)](https://www.youtube.com/watch?v=SeimhEm61hQ)


---


## **The 5 Stages of PubMedR**:
   1. **SETUP**: The user specifies their role and goal, to make the AI suggestions adapted.
   2. **SETTINGS**: Chat & dashboard UI for setting filters, to generate PubMed queries.
   3. **QUERIES**: Mix, match, edit, & generate creative and powerful PubMed queries.
   4. **RESULTS**: Can browse and select individual papers, with quick notes and AI summaries.
   5. **SAVED**: User's selected papers are saved to Google Sheets for easy sharing.

---


## Simply install [UV](https://docs.astral.sh/uv/), clone using Git, type `make install`, then `make run`.


```bash

.PHONY: install install-dev test run

install:
   uv sync
   uv pip install -e .

install-dev:
   uv sync --all-extras
   uv pip install -e .

test:
   uv run pytest --cov=. --cov-fail-under=70

run:
   uv run streamlit run ./src/pubmedr/streamlit_main.py

```

---

## **Why use PubMedR**:
   - I took the initiative to interview multiple regular users of PubMed (Doctors, Pharmacists, Scientists). They revealed two main design challenges to solve:
   - Finding relvent relevant specific information (true positives), with overlapping searches that are specific enough to narrow 1000s down to the best 30 papers to read.
   - Confirming an idea is novel (open to research / publish on) by searching wide enough to check it isn't on PubMed. But can you be SURE? Are there Truly No results, or is that a __False Negative__?
   - PubMedR solves both of these problems, giving very efficient queries, and making it easier to cast much wider search nets.

---

## **Convenient and Transparent**:
   - I interviewed current Roche employees to understand the technical constraints of building real products in Roche. That made me choose to design the data storage centered on Google Sheets, to work in a secure but cloud-native collaborative style.
 
![logfire picture](https://github.com/inn-0/pubmedr/blob/main/assets/Logfire.jpg)

   - Before scaling-up real products, you must quantify their performance & cost. For that I integrated "Logfire": 1. Logfire visualises script errors and successes live, things like 2. LLM inputs/outputs and 3. token counts, which can be 4. aggregated into real-time API-cost dashboards.

---

## **My Background**
- Masters in Chemistry & Mathematics (including two internships at CERN).
- Prior career as a Mathematics & Philosophy Teacher.
- Recent graduate with a Masters in Data Science from a Business School.
- Thesis: Data-Mining Venture Captial Pitchbooks using Multi-Modal LLMs.
- Currently working as a Consulting Data Scientist via my self-employed company, designing LLM pipelines for research scientists at JTI, Geneva.

## **Professional Experience**
- Keenly interested in working on ambitious projects with top collaborators, with an eye towards full-stack / ML Engineering in technical teams.
- First-hand experience in publishing my own scientific research papers, making GenAI tools to support researchers needs.
- Strong User-Centered Design tendencies, feedback-driven approach focused on asking and finding solving key user pain points.

---


## Contents

- __streamilt_main.py__  —  The main UI layout
- __streamlit_components.py__  — Interactive visual elements
- __streamlit.py__ — Interactive functionality & business logic
- __data_models.py__ — Organising data to send to/from Streamlit ←→ LLMs
- __ai_methods.py__ — Structured outputs using Instructor package
- __gdrive.py__ — Google Workspace API methods
- __metapub_methods.py__ — PubMed interface library
- __config.py__ , __constants.py__ , __utils.py__ — Misc.

## .env

I've included a (of course anonymised) placeholder .env file, just to help demonstrate the syntax I use for locally loading my environment secrets (note: .env is listed in the .gitignore for you avoid leaking yours).
