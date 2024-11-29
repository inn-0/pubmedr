# ai_methods.py

from typing import Any, Literal, TypeVar, Union, cast

import instructor
import logfire
from openai import OpenAI
from pydantic import BaseModel

from pubmedr import config
from pubmedr.data_models import (
    S1Setup,
    S2AIJobInputAdvanced,
    S2AIJobInputSimple,
    S2AIJobOutputAdvanced,
    S2AIJobOutputSimple,
    S2Settings,
    S2SettingsSimple,
    S3AIJobInputAdvanced,
    S3AIJobInputSimple,
    S3AIJobOutput,
    S4QuestionAnswer,
)

logger = config.custom_logger(__name__)

# Initialize OpenAI client with proper instrumentation
client = OpenAI(api_key=config.API_KEY_OPENAI)
logfire.instrument_openai(client)
client = instructor.patch(client)

T = TypeVar("T", bound=BaseModel)
SettingsType = Union[S2Settings, S2SettingsSimple]
MessageType = dict[Literal["role", "content"], str]


def clean_none_values(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    """Recursively remove None values from dictionaries and lists."""
    match data:
        case dict():
            return {k: clean_none_values(v) for k, v in data.items() if v is not None}
        case list():
            return [clean_none_values(x) for x in data if x is not None]
        case _:
            return data


@logfire.instrument("run_aijob", extract_args=True)
def run_llm_job(messages: list[MessageType], response_model: type[T]) -> T:
    """Run an LLM job with the given messages and response model."""
    with logfire.span("llm.run"):
        try:
            # Use instructor's response_model directly
            result = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                response_model=response_model,
                max_tokens=4000,
            )

            logger.info(
                "LLM response",
                extra={
                    "result": clean_none_values(result.model_dump() if hasattr(result, "model_dump") else result),
                    "result_type": type(result).__name__,
                },
            )
            return result
        except Exception as e:
            logger.error(
                "OpenAI API error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "messages": messages,
                    "model_type": response_model.__name__,
                },
                exc_info=True,
            )
            raise


def prepare_chat_messages(
    chat_type: str,
    input_data: BaseModel,
) -> list[MessageType]:
    """Prepare chat messages based on chat type."""
    system_prompts = {
        "s2": (
            "Analyze researcher background/goals and update search settings from chat input. "
            "Return updated settings and optionally generate initial PubMed queries. "
            "Provide clear explanations for changes made."
        ),
        "s3": ("Generate focused, specific PubMed queries based on current context and chat input. " "Use existing queries as reference to create variations and alternatives. "),
        "s5": "Analyze the provided paper content and generate insights.",
    }

    return [
        {"role": "system", "content": system_prompts[chat_type]},
        {"role": "user", "content": str(clean_none_values(input_data.model_dump()))},
    ]


def s2_process_chat(
    setup: dict[str, Any],
    settings: dict[str, Any] | None,
    chat_input: str,
    is_advanced: bool = False,
) -> Union[S2AIJobOutputSimple, S2AIJobOutputAdvanced]:
    """Prepare and run S2 (settings) chat."""
    with logfire.span("s2_chat.prepare"):
        # Convert setup dict to match S1Setup fields more efficiently
        setup_model = S1Setup(
            s1_gsheet_id=str(setup.get("gsheet_id")),
            s1_researcher_background=setup.get("researcher_background", ""),
            s1_researcher_goal=setup.get("researcher_goal", ""),
        )

        settings_cls: type[SettingsType] = S2Settings if is_advanced else S2SettingsSimple
        input_model = S2AIJobInputAdvanced if is_advanced else S2AIJobInputSimple
        output_model = S2AIJobOutputAdvanced if is_advanced else S2AIJobOutputSimple

        current_settings = settings_cls(**(settings or {}))
        input_data = input_model(
            setup=setup_model,
            current_settings=cast(Any, current_settings),  # Cast to avoid type check
            chat_input=chat_input,
        )

        result = run_llm_job(
            messages=prepare_chat_messages("s2", input_data),
            response_model=output_model,
        )

        # Initialize empty queries list if needed
        if hasattr(result, "queries"):
            result.queries = result.queries or []

        return result


def s3_process_chat(
    setup: dict[str, Any],
    settings: dict[str, Any],
    chat_input: str,
    current_queries: list[str],
    is_advanced: bool = False,
) -> S3AIJobOutput:
    """Prepare and run S3 (query) chat."""
    with logfire.span("s3_chat.prepare"):
        settings_cls: type[SettingsType] = S2Settings if is_advanced else S2SettingsSimple
        input_model = S3AIJobInputAdvanced if is_advanced else S3AIJobInputSimple

        current_settings = settings_cls(**(settings or {}))
        input_data = input_model(
            search_settings=cast(Any, current_settings),  # Cast to avoid type check
            recent_queries=current_queries,
            chat_input=chat_input,
        )

        result = run_llm_job(
            messages=prepare_chat_messages("s3", input_data),
            response_model=S3AIJobOutput,
        )

        result.queries = result.queries or []
        return result


def s4_question_answer(question: str) -> str:
    """Small simple text-only LLM call"""
    result = run_llm_job(
        messages=[
            {
                "role": "system",
                "content": "Provide a very brief 1-2 sentence summary highlighting key relevance. Be concise.",
            },
            {"role": "user", "content": question},
        ],
        response_model=S4QuestionAnswer,
    )
    return result.answer or ""
