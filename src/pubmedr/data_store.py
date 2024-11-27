# data_store.py

from textual.widgets import Input

from pubmedr.data_models import (
    S1datamodelSetup,
    S2datamodelSettings,
    S3datamodelQueries,
    S4datamodelResults,
    S5datamodelSaved,
)

# Initialize all data model instances to None
s1_setup_data: S1datamodelSetup | None = None
s2_settings_data: S2datamodelSettings | None = None
s3_queries_data: S3datamodelQueries | None = None
s4_results_data: S4datamodelResults | None = None
s5_saved_data: S5datamodelSaved | None = None


def refresh_widget_from_model(widget, data_model) -> None:
    """Generic function to refresh widget contents from a Pydantic model."""
    if data_model:
        model_data = data_model.model_dump()
        widget.app.log.debug(f"Refreshing {widget.__class__.__name__} with data: {model_data}")
        for field_name, value in model_data.items():
            try:
                input_widget = widget.query_one(f"#{field_name}", Input)
                input_widget.value = str(value)
                widget.app.log.debug(f"Updated {field_name} to {value}")
            except Exception as e:
                widget.app.log.error(f"Failed to update {field_name}: {e}")
