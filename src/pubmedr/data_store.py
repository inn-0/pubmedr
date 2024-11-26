# data_store.py

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
