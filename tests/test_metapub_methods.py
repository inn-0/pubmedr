import json
import re

import pytest

from pubmedr import config
from pubmedr.data_models import S4Results
from pubmedr.metapub_methods import fetch_multiple_queries, fetch_pubmed_results

logger = config.custom_logger(__name__)


class TestMetapubMethods:
    class TestSingleQuery:
        @pytest.mark.parametrize(
            "query, max_results, expected_validation",
            [
                (
                    "Doktorova T[au] AND toxicology[Title/Abstract]",
                    5,
                    {
                        "min_results": 1,
                        "required_fields": ["pmid", "title", "authors"],
                        "author_contains": "Doktorova",
                    },
                ),
                (
                    "liver toxicity[Title/Abstract]",
                    3,
                    {
                        "min_results": 1,
                        "required_fields": ["pmid", "title", "abstract"],
                        "keywords_contain": ["liver", "toxicity"],
                    },
                ),
            ],
        )
        def test_fetch_pubmed_results(self, query, max_results, expected_validation):
            logger.info("Testing query: %s", query)
            results = fetch_pubmed_results(query, max_results)

            # Validate results
            assert len(results) > 0, "Should return at least one result"
            assert len(results) <= max_results, f"Should not exceed {max_results} results"

            # Test first result thoroughly
            first_result = results[0]
            assert isinstance(first_result, S4Results)

            # Check required fields
            for field in expected_validation["required_fields"]:
                assert getattr(first_result, field), f"Missing required field: {field}"

            # Check content validations
            if "author_contains" in expected_validation:
                authors_text = " ".join(first_result.authors)
                assert expected_validation["author_contains"] in authors_text

            if "keywords_contain" in expected_validation:
                text_to_search = " ".join(
                    [
                        first_result.title,
                        first_result.abstract or "",
                        " ".join(first_result.keywords),
                    ]
                ).lower()
                for keyword in expected_validation["keywords_contain"]:
                    assert keyword.lower() in text_to_search

            logger.info("First result validation successful")
            logger.info("Title: %s", first_result.title)
            logger.info("Authors: %s", ", ".join(first_result.authors))

            for idx, result in enumerate(results):
                logger.debug(
                    "\nArticle %d:\n"
                    "PMID: %s\n"
                    "Title: %s\n"
                    "Authors: %s\n"
                    "Abstract: %s\n"
                    "Journal: %s\n"
                    "Keywords: %s\n"
                    "MeSH Terms: %s",
                    idx + 1,
                    result.pmid,
                    result.title,
                    ", ".join(result.authors),
                    result.abstract[:200] + "..." if result.abstract else "None",
                    result.journal,
                    ", ".join(result.keywords),
                    ", ".join(result.mesh_terms),
                )

    class TestMultipleQueries:
        @pytest.mark.parametrize(
            "queries, max_results_per_query, expected_validation",
            [
                (
                    [
                        "Doktorova T[au]",
                        "liver toxicity[Title/Abstract]",
                    ],
                    3,
                    {
                        "min_queries_with_results": 1,
                        "expected_authors": ["Doktorova"],
                        "expected_keywords": ["liver", "toxicity"],
                    },
                ),
            ],
        )
        def test_fetch_multiple_queries(self, queries, max_results_per_query, expected_validation):
            logger.info("Testing multiple queries: %s", json.dumps(queries))
            results = fetch_multiple_queries(queries, max_results_per_query)

            # Basic validation
            assert len(results) == len(queries), "Should have results for each query"

            # Count queries with results
            queries_with_results = sum(1 for articles in results.values() if articles)
            assert queries_with_results >= expected_validation["min_queries_with_results"]

            # Validate content across all results
            all_authors = []
            all_keywords = set()  # Using set to collect unique keywords

            for articles in results.values():
                for article in articles:
                    all_authors.extend(article.authors)
                    if article.abstract:
                        # Split on spaces and common punctuation
                        words = re.findall(r"\w+", article.abstract.lower())
                        all_keywords.update(words)
                    # Also check keywords and mesh terms
                    all_keywords.update(k.lower() for k in article.keywords)
                    all_keywords.update(m.lower() for m in article.mesh_terms)

            # Debug logging
            logger.info("Found authors: %s", ", ".join(all_authors))
            logger.info("Found keywords: %s", ", ".join(sorted(all_keywords)))

            # Check expected authors
            for author in expected_validation["expected_authors"]:
                assert any(author in auth for auth in all_authors), f"Author {author} not found in {all_authors}"

            # Check expected keywords with more flexible matching
            for keyword in expected_validation["expected_keywords"]:
                keyword_lower = keyword.lower()
                found = any(keyword_lower in kw for kw in all_keywords)
                if not found:
                    logger.warning(
                        "Keyword '%s' not found in available keywords: %s", keyword, ", ".join(sorted(all_keywords))
                    )
                assert found, f"Keyword {keyword} not found in any article"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
