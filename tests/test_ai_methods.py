import json

import pytest
from logfire.testing import CaptureLogfire

from pubmedr import config
from pubmedr.ai_methods import run_llm_job
from pubmedr.data_models import (
    S2AIJobInputAdvanced,
    S2AIJobInputSimple,
    S2AIJobOutputSimple,
    S2Settings,
    S2SettingsSimple,
    S3AIJobInputAdvanced,
    S3AIJobInputSimple,
    S3AIJobOutput,
    S5AIJobInput,
    S5AIJobOutput,
)

logger = config.custom_logger(__name__)


@pytest.fixture(autouse=True)
def setup_logging(capfire: CaptureLogfire):
    """Set up logging for all tests in this module."""
    capfire.exporter.clear()  # Clear any previous spans
    yield
    # Optional: Print or assert on logs after test
    for span in capfire.exporter.exported_spans:
        print(f"Log: {span.name}")


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
        def test_s2_simple(self, caplog, settings_data, chat_input, expected_keywords):
            current_settings = S2SettingsSimple(**settings_data)
            input_model = S2AIJobInputSimple(current_settings=current_settings, chat_input=chat_input)

            logger.info("Running S2 simple test with input: %s", input_model.model_dump_json(indent=2))
            result = run_llm_job("s2_simple", json.dumps(input_model.model_dump()))

            assert "Running S2 simple test with input" in caplog.text

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
            current_settings = S2Settings(**settings_data)
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
                    S2Settings,
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

    def test_logging_structure(self, capfire: CaptureLogfire):
        # Your test code that generates logs...

        exported_data = capfire.exporter.exported_spans_as_dict(strip_filepaths=True, include_resources=False)

        # Assert on the structure
        assert any(span["attributes"].get("logfire.msg", "").startswith("Running LLM job") for span in exported_data)


# # ai_methods.py

# from functools import wraps
# from typing import Any

# import instructor
# import logfire
# from openai import OpenAI
# from pydantic import BaseModel

# from pubmedr import config
# from pubmedr.data_models import (
#     S2AIJobInputAdvanced,
#     S2AIJobInputSimple,
#     S2AIJobOutputAdvanced,
#     S2AIJobOutputSimple,
#     S3AIJobInputAdvanced,
#     S3AIJobInputSimple,
#     S3AIJobOutput,
# )

# logger = config.custom_logger(__name__)

# # Initialize OpenAI client with instrumentation
# client = OpenAI(api_key=config.API_KEY_OPENAI)
# logfire.instrument_openai(client)
# client = instructor.from_openai(client)


# class S2Response(BaseModel):
#     """Response model for settings updates."""

#     updated_settings: dict[str, Any]
#     initial_queries: list[str] = []
#     explanation: str


# class S3Response(BaseModel):
#     """Response model for query generation."""

#     queries: list[str]
#     explanation: str


# def log_payload(func):
#     """Decorator to log function inputs and outputs."""

#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         with logfire.span(f"{func.__name__}_detailed"):
#             # Clean and prepare input data
#             input_data = {
#                 "args": [
#                     arg.model_dump()
#                     if hasattr(arg, "model_dump")
#                     else str(arg)
#                     if not isinstance(arg, (dict, list))
#                     else arg
#                     for arg in args
#                 ],
#                 "kwargs": {
#                     k: v.model_dump() if hasattr(v, "model_dump") else str(v) if not isinstance(v, (dict, list)) else v
#                     for k, v in kwargs.items()
#                 },
#             }

#             logger.debug(
#                 "Function input",
#                 extra={
#                     "function": func.__name__,
#                     "payload": clean_none_values(input_data),
#                     "arg_types": {k: type(v).__name__ for k, v in kwargs.items()},
#                 },
#             )

#             try:
#                 result = func(*args, **kwargs)
#                 output_data = result.model_dump() if hasattr(result, "model_dump") else str(result)
#                 logger.debug(
#                     "Function output",
#                     extra={
#                         "function": func.__name__,
#                         "result": clean_none_values(output_data),
#                         "result_type": type(result).__name__,
#                     },
#                 )
#                 return result
#             except Exception as e:
#                 logger.error(
#                     "Function failed",
#                     extra={
#                         "function": func.__name__,
#                         "error": str(e),
#                         "error_type": type(e).__name__,
#                         "input_payload": clean_none_values(input_data),
#                     },
#                     exc_info=True,
#                 )
#                 raise

#     return wrapper


# def clean_none_values(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
#     """Recursively remove None values from dictionaries and lists."""
#     if isinstance(data, dict):
#         return {k: clean_none_values(v) for k, v in data.items() if v is not None}
#     elif isinstance(data, list):
#         return [clean_none_values(x) for x in data if x is not None]
#     return data


# @log_payload
# @logfire.instrument("process_s2_chat", extract_args=True)
# def process_s2_chat(
#     setup: dict,
#     settings: dict,
#     chat_input: str,
#     is_advanced: bool = False,
# ) -> S2AIJobOutputSimple | S2AIJobOutputAdvanced:
#     """Process chat input to update settings and generate initial queries."""
#     # Create proper input model
#     input_model = S2AIJobInputAdvanced if is_advanced else S2AIJobInputSimple
#     output_model = S2AIJobOutputAdvanced if is_advanced else S2AIJobOutputSimple

#     input_data = input_model(
#         setup=setup,
#         current_settings=settings,
#         chat_input=chat_input,
#     )

#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "Analyze researcher background/goals and update search settings from chat input. "
#                 "Return updated settings and optionally generate initial PubMed queries. "
#                 "Provide clear explanations for changes made."
#             ),
#         },
#         {
#             "role": "user",
#             "content": str(clean_none_values(input_data.model_dump())),
#         },
#     ]

#     try:
#         result = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages,
#             response_model=output_model,
#             max_tokens=4000,
#             temperature=0.7,
#         )
#         return result
#     except Exception as e:
#         logger.error("Failed to process settings chat", extra={"error": str(e)}, exc_info=True)
#         raise


# @log_payload
# @logfire.instrument("process_s3_chat", extract_args=True)
# def process_s3_chat(
#     setup: dict,
#     settings: dict,
#     chat_input: str,
#     current_queries: list[str],
#     is_advanced: bool = False,
# ) -> S3AIJobOutput:
#     """Process chat input to generate new PubMed queries."""
#     # Create proper input model
#     input_model = S3AIJobInputAdvanced if is_advanced else S3AIJobInputSimple

#     input_data = input_model(
#         search_settings=settings,
#         recent_queries=current_queries,
#         chat_input=chat_input,
#     )

#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "Generate focused, specific PubMed queries based on current context and chat input. "
#                 "Use existing queries as reference to create variations and alternatives. "
#                 "Provide explanations for the generated queries."
#             ),
#         },
#         {
#             "role": "user",
#             "content": str(clean_none_values(input_data.model_dump())),
#         },
#     ]

#     try:
#         result = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages,
#             response_model=S3AIJobOutput,
#             max_tokens=4000,
#             temperature=0.7,
#         )
#         return result
#     except Exception as e:
#         logger.error("Failed to process query chat", extra={"error": str(e)}, exc_info=True)
#         raise


# @logfire.instrument("run_aijob", extract_args=True)
# def run_llm_job(request_type: str, input_data: str | dict) -> Any:
#     # Clean input data if it's a dictionary
#     if isinstance(input_data, dict):
#         input_data = clean_none_values(input_data)
#     elif not isinstance(input_data, str):
#         raise TypeError(f"input_data must be str or dict, not {type(input_data)}")

#     def get_response_model(request_type: str):
#         model = RESPONSE_MODEL_MAPPING.get(request_type)
#         if model is None:
#             raise KeyError(f"No response model found for request type: {request_type}")
#         return model

#     with logfire.span(f"llm_job.{request_type}"):
#         logger.info("Running LLM job with request type: %s", request_type)
#         logger.info("Input data: %s", input_data)

#         response_model_cls = get_response_model(request_type)
#         messages: list[ChatCompletionMessageParam] = [
#             {
#                 "role": "system",
#                 "content": "Answer in JSON.",
#             },
#             {"role": "user", "content": input_data},
#         ]

#         try:
#             # Run the LLM call using the instructor client
#             result, completion = client.chat.completions.create_with_completion(
#                 model="gpt-4o-mini",  # HARDCODED
#                 messages=messages,
#                 max_tokens=4000,
#                 temperature=0.1,
#                 response_model=response_model_cls,
#             )

#             if completion.usage:
#                 logger.info(
#                     "Token usage",
#                     extra={
#                         "tokens": completion.usage.model_dump(),  # Simplified token logging
#                     },
#                 )

#             return result
#         except Exception as e:
#             logger.error("OpenAI API error: %s", e, exc_info=True)
#             raise
