import json
import logging
import pytest
from pubmedr.data_models import (
    S2datamodelSettingsSimple,
    S2datamodelSettings,
    S2AIJobInputSimple,
    S2AIJobInputAdvanced,
    S3AIJobInputSimple,
    S3AIJobInputAdvanced,
    S3AIJobOutput,
    S5AIJobInput,
    S2AIJobOutputSimple,
    S5AIJobOutput,
)
from pubmedr.ai_methods import run_llm_job

logger = logging.getLogger(__name__)


class TestLLMJobs:
    class TestS2Simple:
        @pytest.mark.parametrize(
            "settings_data, chat_input, expected_keywords",
            [
                (
                    {
                        "keywords": "Triclosan",
                        "author": "",
                        "date_range": "last 5 years",
                        "text_availability": "hasabstract",
                        "exclusions": [],
                    },
                    "Find articles on Triclosan and genotoxicity.",
                    ["Triclosan", "genotoxicity"],
                ),
            ],
        )
        def test_s2_simple(self, settings_data, chat_input, expected_keywords):
            current_settings = S2datamodelSettingsSimple(**settings_data)
            input_model = S2AIJobInputSimple(current_settings=current_settings, chat_input=chat_input)

            logger.info("Running S2 simple test with input: %s", input_model.model_dump_json())
            result = run_llm_job("s2_simple", json.dumps(input_model.model_dump()))

            logger.info("Received result with settings: %s", result.updated_settings.model_dump_json())
            assert isinstance(result, S2AIJobOutputSimple)
            for keyword in expected_keywords:
                assert keyword in result.updated_settings.keywords
                logger.info("Verified keyword '%s' in results", keyword)

    class TestS2Advanced:
        @pytest.mark.parametrize(
            "settings_data, chat_input, expected_results",
            [
                (
                    {
                        "keywords": "Piperonyl Butoxide",
                        "author": "",
                        "date_range": "last 5 years",
                        "text_availability": "hasabstract",
                        "exclusions": ["Review"],
                        "complex_boolean": True,
                        "species": "Humans",
                        "mesh_terms": [],
                        "publication_types": [],
                        "result_limit": 500,
                    },
                    "Search for articles on hepatotoxicity in humans, excluding reviews, with abstracts available.",
                    {
                        "keywords": "hepatotoxicity",
                        "exclusions": ["Review"],
                        "species": "Humans",
                        "text_availability": "hasabstract",
                    },
                ),
            ],
        )
        def test_s2_advanced(self, settings_data, chat_input, expected_results):
            current_settings = S2datamodelSettings(**settings_data)
            input_model = S2AIJobInputAdvanced(current_settings=current_settings, chat_input=chat_input)

            logger.info("Running S2 advanced test with input: %s", input_model.model_dump_json())
            result = run_llm_job("s2_advanced", json.dumps(input_model.model_dump()))

            updated_settings = result.updated_settings
            logger.info("Received updated settings: %s", updated_settings.model_dump_json())

            for field, value in expected_results.items():
                current_value = getattr(updated_settings, field)
                logger.info("Checking field '%s': expected=%s, got=%s", field, value, current_value)

                if isinstance(value, list):
                    assert all(item in current_value for item in value), f"Missing items in {field}"
                else:
                    assert value in str(current_value), f"Expected {value} in {field}, got {current_value}"

    class TestS3Queries:
        @pytest.mark.parametrize(
            "request_type, settings_model, settings_data, recent_queries, chat_input, expected_content",
            [
                # ... first test case ...
                (
                    "s3_advanced",
                    S2datamodelSettings,
                    {
                        "keywords": "in vitro models",
                        "author": "",
                        "date_range": "last 10 years",
                        "text_availability": "hasabstract",
                        "exclusions": [],
                        "complex_boolean": True,
                        "last_author": "Doktorova T",
                        "proximity_search_terms": "carcinogenicity",
                        "proximity_distance": 10,
                        "affiliation_excludes": ["China"],
                    },
                    [
                        'Doktorova T[lastau] AND "in vitro models carcinogenicity"[Title/Abstract:~10] NOT China[Affiliation]'
                    ],
                    "Focus on studies excluding affiliations from China.",
                    "china[affiliation]",
                ),
            ],
        )
        def test_s3_queries(
            self, request_type, settings_model, settings_data, recent_queries, chat_input, expected_content
        ):
            search_settings = settings_model(**settings_data)
            input_model = (S3AIJobInputSimple if request_type == "s3_simple" else S3AIJobInputAdvanced)(
                search_settings=search_settings,
                recent_queries=recent_queries,
                chat_input=chat_input,
            )

            logger.info(
                "Running S3 query test with type '%s' and input: %s", request_type, input_model.model_dump_json()
            )
            result = run_llm_job(request_type, json.dumps(input_model.model_dump()))

            logger.info("Received queries: %s", result.new_queries)

            assert isinstance(result, S3AIJobOutput)
            assert result.new_queries is not None

            found = any(expected_content in query.lower() for query in result.new_queries)
            logger.info("Checking for '%s' in queries: %s", expected_content, found)
            assert found, f"Expected {expected_content} in one of the queries: {result.new_queries}"

    class TestS5Content:
        @pytest.mark.parametrize(
            "content",
            [
                "Title: CRISPR Technology in Gene Editing\nAbstract: CRISPR/Cas9 has revolutionized gene editing...",
            ],
        )
        def test_s5_content(self, content):
            input_model = S5AIJobInput(content=content)

            logger.info("Running S5 content test with input: %s", input_model.model_dump_json())
            result = run_llm_job("s5", json.dumps(input_model.model_dump()))

            logger.info("Received answer of length: %d", len(result.answer or ""))

            assert isinstance(result, S5AIJobOutput)
            assert result.answer is not None
            assert len(result.answer) > 0
