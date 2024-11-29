from datetime import datetime

INFO_BAR_BUTTONS = [
    {
        "name": "Copy",
        "feather": "Copy",
        "hasText": True,
        "alwaysOn": True,
        "commands": ["copyAll", ["infoMessage", {"text": "Copied!", "timeout": 200, "classToggle": "show"}]],
        "style": {"right": "10.5rem"},
    },
    # {
    #     "name": "Run",
    #     "feather": "Play",
    #     "hasText": True,
    #     "alwaysOn": True,
    #     "commands": ["submit"],
    #     "style": {"right": "5.5rem"},
    # },
    {
        "name": "Save",
        "feather": "Save",
        "hasText": True,
        "alwaysOn": True,
        "commands": [
            ["response", {"text": "Saved!", "timeout": 500, "classToggle": "show"}],
            "submit",
        ],
        "style": {"right": "0.4rem"},
    },
]


PUBMED_COMPLETIONS = [
    # Boolean Operators (highest priority)
    {"caption": "AND", "value": "AND ", "meta": "Boolean", "score": 100},
    {"caption": "OR", "value": "OR ", "meta": "Boolean", "score": 100},
    {"caption": "NOT", "value": "NOT ", "meta": "Boolean", "score": 100},
    # Common Author Fields
    {"caption": "[1au]", "value": "[1au]", "meta": "First Author", "score": 90},
    {"caption": "[lastau]", "value": "[lastau]", "meta": "Last Author", "score": 90},
    {"caption": "[au]", "value": "[Author]", "meta": "Author", "score": 90},
    {"caption": "[ad]", "value": "[Affiliation]", "meta": "Affiliation", "score": 90},
    # Basic Search Fields
    {"caption": "[ti]", "value": "[Title]", "meta": "Field", "score": 85},
    {"caption": "[ab]", "value": "[Abstract]", "meta": "Field", "score": 85},
    {"caption": "[tiab]", "value": "[Title/Abstract]", "meta": "Field", "score": 85},
    {"caption": "[tw]", "value": "[Text Word]", "meta": "Field", "score": 85},
    # Study Type Fields
    {"caption": "[pt]", "value": "[Publication Type]", "meta": "Type", "score": 75},
    {"caption": "Clinical Trial[pt]", "value": "Clinical Trial[pt]", "meta": "Type", "score": 75},
    {"caption": "Review[pt]", "value": "Review[pt]", "meta": "Type", "score": 75},
    {"caption": "Case Reports[pt]", "value": "Case Reports[pt]", "meta": "Type", "score": 75},
    # Common Study Models
    {"caption": "in vitro[tiab]", "value": '"in vitro"[tiab]', "meta": "Model", "score": 55},
    {"caption": "in vivo[tiab]", "value": '"in vivo"[tiab]', "meta": "Model", "score": 55},
    {"caption": "in silico[tiab]", "value": '"in silico"[tiab]', "meta": "Model", "score": 55},
    # Common Toxicology Endpoints
    {"caption": "genotoxicity[tiab]", "value": "genotoxicity[tiab]", "meta": "Endpoint", "score": 50},
    {"caption": "cytotoxicity[tiab]", "value": "cytotoxicity[tiab]", "meta": "Endpoint", "score": 50},
    {"caption": "hepatotoxicity[tiab]", "value": "hepatotoxicity[tiab]", "meta": "Endpoint", "score": 50},
    {"caption": "neurotoxicity[tiab]", "value": "neurotoxicity[tiab]", "meta": "Endpoint", "score": 50},
    {"caption": "cardiotoxicity[tiab]", "value": "cardiotoxicity[tiab]", "meta": "Endpoint", "score": 50},
    # Proximity Search Templates
    {"caption": "prox~10", "value": '""[tiab:~10]', "meta": "Proximity", "score": 45},
    # Common Filters
    {"caption": "hasabstract", "value": "hasabstract", "meta": "Filter", "score": 40},
    {"caption": "humans[mh]", "value": "humans[mh]", "meta": "Filter", "score": 40},
    {"caption": "animals[mh]", "value": "animals[mh]", "meta": "Filter", "score": 40},
    {"caption": "english[la]", "value": "english[la]", "meta": "Filter", "score": 40},
]

INFO_BAR = {
    "name": "language info",
    "css": """
        background-color: #B8D1E6;  /* Lighter version of Roche blue #007AB8 */
        display: flex;
        align-items: center;

        body > #root .ace-streamlit-dark~& {
            background-color: #262830;
        }

        .ace-streamlit-dark~& span {
            color: #fff;
            opacity: 0.6;
        }

        span {
            color: #1A1A1A;
            opacity: 0.8;
        }
    """,
    "style": {
        "width": "100%",
        "padding": "0.5rem 0.75rem",
        "borderRadius": "8px 8px 0px 0px",
    },
    "info": [{"name": "PubMedR", "style": {"width": "100px"}}],
}

STYLING_BUTTONS = """
    <style>
    /* Remove color theming from big UI buttons */
    [data-testid="stButton"] button {
        background-color: inherit;
        color: inherit;
    }
    /* Style only the specific buttons we want themed */
    [data-testid="stButton"]:has(button:contains("Run Merged")),
    [data-testid="stButton"]:has(button:contains("Run Selected")),
    [data-testid="stButton"]:has(button:contains("Delete Selected")) {
        background-color: #007AB8;
        color: white;
    }
    [data-testid="stButton"]:has(button:contains("Run Merged")):hover,
    [data-testid="stButton"]:has(button:contains("Run Selected")):hover,
    [data-testid="stButton"]:has(button:contains("Delete Selected")):hover {
        background-color: #005A8C;
    }
    /* Add border around code editor */
    .stCodeBlock {
        border: 1px solid #007AB8;
        border-radius: 5px;
    }
    </style>
"""


MOCK_DATA = {
    "setup": {
        "gsheet_id": "1v2z0ZyZMmQS91V42McA_mS42r562PHSNt32nqVjzzrU",
        "sheet_name": "data",
        "researcher_background": "Toxicology researcher specialised in in-vivo and in-silico modelling.",
        "research_goal": "Investigating Triclosan effects in hepatic models, currently I'm thinking to find ...",
    },
    "queries": [
        "Doktorova T[1au] \nAND (Triclosan[Substance Name] OR Triclosan[Title/Abstract]) \nAND (genotoxicity[Title/Abstract] OR toxicity[Title/Abstract])",
        "(Piperonyl Butoxide[Substance Name] OR PBO[Title/Abstract]) \nAND hepatotoxicity[Title/Abstract] \nAND Humans[MeSH Terms] \nNOT Review[Publication Type] \nAND hasabstract",
        'Doktorova T[lastau] \nAND "in vitro models carcinogenicity"[Title/Abstract:~10] \nNOT China[Affiliation]',
    ],
    "results": [
        {
            "query": "Doktorova T[1au] AND (Triclosan[Substance Name] OR Triclosan[Title/Abstract]) AND (genotoxicity[Title/Abstract] OR toxicity[Title/Abstract])",
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "pmid": "35679121",
                    "title": "How to Foster 'New Approach Methodology' Toxicologists",
                    "authors": [
                        "Doktorova TY",
                        "Azzi P",
                        "Hofer J",
                        "Messner CJ",
                        "Gaiser C",
                        "Werner S",
                        "Singh P",
                        "Hardy B",
                        "Suter-Dick L",
                        "Chesne C",
                    ],
                    "first_author": "Doktorova TY",
                    "last_author": "Chesne C",
                    "abstract": "The need to reduce, refine and replace animal experimentation has led to a boom in the establishment of new approach methodologies (NAMs)...",
                    "journal": "Altern Lab Anim",
                    "pub_date": datetime(2022, 1, 1),
                    "doi": "10.1177/02611929221103713",
                    "keywords": ["NAMs", "toxicology", "education"],
                    "mesh_terms": ["Education", "Toxicology", "Methods"],
                    "publication_types": ["Journal Article"],
                    "is_free": True,
                    "affiliations": ["Vrije Universiteit Brussel"],
                },
                {
                    "pmid": "32976933",
                    "title": "A semi-automated workflow for adverse outcome pathway hypothesis generation",
                    "authors": ["Doktorova TY", "Oki NO", "Mohorič T", "Exner TE", "Hardy B"],
                    "first_author": "Doktorova TY",
                    "last_author": "Hardy B",
                    "abstract": "The utility of the Adverse Outcome Pathway (AOP) concept has been largely recognized by scientists...",
                    "journal": "Regul Toxicol Pharmacol",
                    "pub_date": datetime(2020, 1, 1),
                    "doi": "10.1016/j.yrtph.2020.104823",
                    "keywords": ["AOP", "toxicology", "workflow"],
                    "mesh_terms": ["Adverse Outcome Pathways", "Toxicology"],
                    "publication_types": ["Journal Article"],
                    "is_free": False,
                    "affiliations": ["Edelweiss Connect GmbH"],
                },
            ],
        },
        # ... similar updates for other result groups ...
    ],
}
