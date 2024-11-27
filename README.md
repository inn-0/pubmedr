
# Live Demo

https://pubmedr.replit.app

# Install & Run
```bash
uv add metapub pydantic pytest pytest-cov pytest-asyncio textual textual-dev textual[syntax] pandas google-api-python-client google-auth gspread gspread-dataframe gspread-formatting requests urllib3 logfire instructor openai

uv run ./src/pubmedr/main.py
```

---

My backround: Masters in Chemistry & Mathematics (2 internships at CERN), worked as a Mathematics & Philosophy Teacher, recent graduate from a Masters in Data Science, currently working as a Consulting Data Scientist via my own self-employed company.

I am currently working on a project for JTI in Geneva, designing LLM pipelines for their reserach scientists. So I have first hand experience of publishing my own scientific resrach papers, and of knowing how reserachers use Pubmed, and what could make that usage better.

I use a Design Thinking approach, starting with going to users and finding their pain points. So I interviewed a former classmate who currently works in Roche Basel, and a practicing doctor who uses Pubmed regularly.

The main design decisions I got from their feedback were:
1. Use Google Drive for data serialisation, to Google Sheets not locally, becuase this is the expected best practice in Roche
2. Users search pubmed primarily either to A. find out specific information (true positive), or to B. find no results and decide that their idea is novel and worth pursuing, for which it is very important to have sufficently broad searches (need to avoid false negative)
3. Deploy in a format that is cross-platform compatible and lightweight. 'Textual' was chosen because it can be run locally, or also conveniently deployed to Replit (or Google Cloud Platform)


There are 5 stages in my app:
1. SETUP: User specifies their role and goal
2. SETTINGS: User interacts with the (chat) UI to specify their filters
3. QUERIES: It uses those filters to generate pubmed queries (using the metapub package)
4. RESULTS: Users can browse and select individual results to save and add notes to
5. SAVED: Users can browse their saved results, either in the app, or in Google Sheets
