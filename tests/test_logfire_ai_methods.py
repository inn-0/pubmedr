import json
import logging
import logfire
from logfire.testing import TestExporter

from pubmedr.data_models import (
    S2AIJobInputSimple,
    S2SettingsSimple,
)
from pubmedr.ai_methods import run_llm_job

from pubmedr import config

logger = config.custom_logger(__name__)

def test_s2_simple_logging():
    # Set up logfire capture
    exporter = TestExporter()
    exporter.clear()
T
    # Test data
    settings_data = {
        "keywords": "Triclosan",
        "author": "",
        "date_range": "last 5 years",
        "text_availability": "hasabstract",
        "exclusions": [],
    }
    chat_input = "Find articles on Triclosan and genotoxicity."

    # Create test input and run with span tracking
    with logfire.span("test_s2_simple"):
        current_settings = S2SettingsSimple(**settings_data)
        input_model = S2AIJobInputSimple(
            current_settings=current_settings,
            chat_input=chat_input,
        )

        # Run the job
        logger.info("Running test with input: %s", input_model.model_dump_json(indent=2))
        result = run_llm_job("s2_simple", json.dumps(input_model.model_dump()))

        # Log the result
        logger.info("Received result: %s", result.model_dump_json())

    # Check the logs
    exported_data = exporter.exported_spans_as_dict(
        strip_filepaths=True,
        include_resources=False,
    )

    # Print captured spans for debugging
    for span in exported_data:
        print(f"Captured span: {span['name']}")
        print(f"Attributes: {span['attributes']}")

    # Verify OpenAI calls were logged
    openai_spans = [
        span for span in exported_data
        if span["attributes"].get("openai.request.model") is not None
    ]
    print(f"Found {len(openai_spans)} OpenAI spans")

if __name__ == "__main__":
    test_s2_simple_logging()
