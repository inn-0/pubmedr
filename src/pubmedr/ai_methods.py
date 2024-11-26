# ai_methods.py

import logging
from pubmedr import config
from typing import Any


import instructor
import logfire
from logfire.integrations.logging import LogfireLoggingHandler
from openai import OpenAI
from pubmedr.data_models import (
    S2AIJobOutputSimple,
    S2AIJobOutputAdvanced,
    S3AIJobOutput,
    S5AIJobOutput,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
    handlers=[LogfireLoggingHandler()],
)

client = instructor.from_openai(OpenAI(api_key=config.API_KEY_OPENAI))

RESPONSE_MODEL_MAPPING = {
    "s2_simple": S2AIJobOutputSimple,
    "s2_advanced": S2AIJobOutputAdvanced,
    "s3_simple": S3AIJobOutput,
    "s3_advanced": S3AIJobOutput,
    "s5": S5AIJobOutput,
}


@logfire.instrument("run_aijob", extract_args=True)
def run_llm_job(request_type: str, input_data: str) -> Any:
    logging.info(f"Running LLM job with request type: {request_type}")

    def get_response_model(request_type: str):
        model = RESPONSE_MODEL_MAPPING.get(request_type)
        if model is None:
            raise KeyError(f"No response model found for request type: {request_type}")
        return model

    response_model_cls = get_response_model(request_type)
    if response_model_cls is None:
        raise ValueError(f"Invalid request type: {request_type}")

    messages = [
        {
            "role": "system",
            "content": "You are an assistant that processes user input and returns structured data in JSON.",
        },
        {"role": "user", "content": input_data},
    ]

    try:
        # Run the LLM call using the instructor client
        result, completion = client.chat.completions.create_with_completion(
            model="gpt-4o-mini",  # HARDCODED
            messages=messages,
            max_tokens=4000,
            temperature=0.1,
            response_model=response_model_cls,
        )

        if completion.usage:
            logging.info(
                "Token usage",
                extra={
                    "tokens": {
                        "prompt": completion.usage.prompt_tokens,
                        "completion": completion.usage.completion_tokens,
                        "total": completion.usage.total_tokens,
                        "details": {
                            "completion": {
                                "audio": completion.usage.completion_tokens_details.audio_tokens,
                                "reasoning": completion.usage.completion_tokens_details.reasoning_tokens,
                            },
                            "prompt": {
                                "audio": completion.usage.prompt_token_details.audio_tokens,
                                "cached": completion.usage.prompt_token_details.cached_tokens,
                            },
                        },
                    },
                },
            )

        return result
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        raise
