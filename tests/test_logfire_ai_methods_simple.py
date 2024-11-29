import json

from pubmedr.ai_methods import run_llm_job
from pubmedr.data_models import S2AIJobInputSimple, S2SettingsSimple


def main():
    """Simple test of the AI methods with minimal setup."""
    # Basic test data
    settings = S2SettingsSimple(
        keywords="aspirin",
        author="",
        date_range="last 5 years",
        text_availability="hasabstract",
        exclusions=[],
    )

    # Create input model
    input_model = S2AIJobInputSimple(
        current_settings=settings,
        chat_input="Find articles about aspirin and heart disease",
    )

    # Run the job
    print("Sending request...")
    result = run_llm_job(
        request_type="s2_simple",
        input_data=json.dumps(input_model.model_dump()),
    )

    # Print results
    print("\nResults:")
    print(f"Updated keywords: {result.updated_settings.keywords}")
    print(f"Updated settings: {result.updated_settings.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()
